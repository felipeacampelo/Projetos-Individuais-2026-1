from __future__ import annotations

import hashlib

import fitz
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import (
    Company,
    MetricCatalogAlias,
    MetricCatalogItem,
    MonitoringJob,
    PublicationSource,
    PublicationSignal,
    ResultDocument,
    ExtractionRun,
)
from app.extraction.service import DocumentSemanticProcessingResult
from app.ingestion.fetchers.document_fetcher import DocumentFetchError, FetchedDocument
from app.ingestion.jobs import MonitoringJobService


class StubResultsPageFetcher:
    def __init__(self, html_by_url: dict[str, str]) -> None:
        self.html_by_url = html_by_url

    def fetch_html(self, url: str) -> str:
        return self.html_by_url[url]


class StubDocumentFetcher:
    def __init__(self, payloads_by_url: dict[str, bytes], failing_urls: set[str] | None = None) -> None:
        self.payloads_by_url = payloads_by_url
        self.failing_urls = failing_urls or set()

    def fetch(self, url: str) -> FetchedDocument:
        if url in self.failing_urls:
            raise DocumentFetchError("synthetic fetch failure")
        return FetchedDocument(
            source_url=url,
            effective_url=url,
            content=self.payloads_by_url[url],
            content_type="application/pdf",
        )


class StubSemanticProcessingService:
    def __init__(self, result: DocumentSemanticProcessingResult) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def process_document(
        self,
        *,
        result_document_id: int,
        content: bytes,
        source_url: str,
        document_type: str,
    ) -> DocumentSemanticProcessingResult:
        self.calls.append(
            {
                "result_document_id": result_document_id,
                "content": content,
                "source_url": source_url,
                "document_type": document_type,
            }
        )
        return self.result


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def build_pdf_bytes(text_lines: list[str]) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "\n".join(text_lines))
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def seed_company_and_source(session: Session) -> Company:
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    session.add(
        PublicationSource(
            company_id=company.id,
            name="Central de Resultados MRV",
            source_type="results_page",
            url="https://ri.example.com/resultados",
            priority=10,
            is_active=True,
        )
    )
    session.commit()
    return company


def seed_metric_catalog(session: Session) -> None:
    vso = MetricCatalogItem(
        slug="vso",
        name="VSO",
        category="operacional_comercial",
        canonical_unit="percentage",
        is_active=True,
    )
    vendas = MetricCatalogItem(
        slug="vendas-liquidas",
        name="Vendas Líquidas",
        category="operacional_comercial",
        canonical_unit="brl",
        is_active=True,
    )
    session.add_all([vso, vendas])
    session.flush()
    session.add_all(
        [
            MetricCatalogAlias(metric_catalog_item_id=vso.id, alias="vso"),
            MetricCatalogAlias(metric_catalog_item_id=vendas.id, alias="vendas líquidas"),
            MetricCatalogAlias(metric_catalog_item_id=vendas.id, alias="vendas liquidas"),
        ]
    )
    session.commit()


def test_run_job_discovers_and_deduplicates_documents() -> None:
    session = build_session()
    seed_company_and_source(session)
    html = """
    <html>
      <body>
        <a href="/docs/previa-1.pdf">Prévia Operacional 1T26</a>
        <a href="/docs/reupload-previa-1.pdf">Prévia Operacional 1T26 republicada</a>
      </body>
    </html>
    """
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher(
            {"https://ri.example.com/resultados": html}
        ),
        document_fetcher=StubDocumentFetcher(
            {
                "https://ri.example.com/docs/previa-1.pdf": b"same-pdf-content",
                "https://ri.example.com/docs/reupload-previa-1.pdf": b"same-pdf-content",
            }
        ),
    )

    result = service.run_job(scope_type="company", scope_value="mrv")

    assert result.status == "completed"
    assert result.discovered_signal_count == 2
    assert result.recovered_document_count == 1
    assert result.duplicate_document_count == 1
    assert result.recovery_failed_count == 0

    jobs = session.scalars(select(MonitoringJob)).all()
    assert len(jobs) == 1
    assert jobs[0].status == "completed"
    assert jobs[0].finished_at is not None

    signals = session.scalars(select(PublicationSignal).order_by(PublicationSignal.id.asc())).all()
    assert [signal.processing_status for signal in signals] == [
        "content_recovered",
        "duplicate_content",
    ]

    documents = session.scalars(select(ResultDocument)).all()
    assert len(documents) == 1
    assert documents[0].document_type == "previa_operacional"


def test_run_job_marks_partial_failure_when_document_recovery_fails() -> None:
    session = build_session()
    seed_company_and_source(session)
    html = """
    <html>
      <body>
        <a href="/docs/failing.pdf">Prévia Operacional 1T26</a>
      </body>
    </html>
    """
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher(
            {"https://ri.example.com/resultados": html}
        ),
        document_fetcher=StubDocumentFetcher({}, failing_urls={"https://ri.example.com/docs/failing.pdf"}),
    )

    result = service.run_job(scope_type="company", scope_value="mrv")

    assert result.status == "completed_with_errors"
    assert result.discovered_signal_count == 1
    assert result.recovered_document_count == 0
    assert result.duplicate_document_count == 0
    assert result.recovery_failed_count == 1

    jobs = session.scalars(select(MonitoringJob)).all()
    assert len(jobs) == 1
    assert jobs[0].status == "completed_with_errors"
    assert jobs[0].failure_stage == "recovery"
    assert jobs[0].failure_reason == "recovery_failed_count=1"

    signals = session.scalars(select(PublicationSignal)).all()
    assert len(signals) == 1
    assert signals[0].processing_status == "recovery_failed"
    assert signals[0].failure_stage == "recovery"
    assert signals[0].failure_reason == "synthetic fetch failure"


def test_run_job_canonicalizes_parseable_pdf() -> None:
    session = build_session()
    seed_company_and_source(session)
    seed_metric_catalog(session)
    html = """
    <html>
      <body>
        <a href="/docs/previa-1.pdf">Prévia Operacional 1T26</a>
      </body>
    </html>
    """
    pdf_bytes = build_pdf_bytes(
        [
            "MRV 1T26 Prévia Operacional",
            "VSO 12,5%",
            "Vendas Líquidas R$ 500 milhões",
        ]
    )
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher({"https://ri.example.com/resultados": html}),
        document_fetcher=StubDocumentFetcher({"https://ri.example.com/docs/previa-1.pdf": pdf_bytes}),
    )

    result = service.run_job(scope_type="company", scope_value="mrv")

    assert result.status == "completed"
    assert result.recovered_document_count == 1
    assert result.extracted_document_count == 1
    assert result.canonical_document_count == 1

    documents = session.scalars(select(ResultDocument)).all()
    assert len(documents) == 1
    assert documents[0].current_state == "canonical"

    canonical_metrics = session.scalars(select(models.CanonicalMetric)).all()
    assert len(canonical_metrics) >= 2


def test_run_job_records_interpretation_failure_reason_on_signal() -> None:
    session = build_session()
    seed_company_and_source(session)
    html = """
    <html>
      <body>
        <a href="/docs/previa-1.pdf">Prévia Operacional 1T26</a>
      </body>
    </html>
    """
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher({"https://ri.example.com/resultados": html}),
        document_fetcher=StubDocumentFetcher({"https://ri.example.com/docs/previa-1.pdf": b"pdf-content"}),
    )
    service.document_semantic_processing_service = StubSemanticProcessingService(
        DocumentSemanticProcessingResult(
            extraction_status="interpretation_failed",
            document_state="interpretation_failed",
            canonical_metric_count=0,
            failed_fact_count=0,
            extraction_run_id=None,
            failure_stage="interpretation",
            failure_reason="pdf_text_not_extractable",
        )
    )

    result = service.run_job(scope_type="company", scope_value="mrv")

    assert result.status == "completed"
    jobs = session.scalars(select(MonitoringJob)).all()
    assert len(jobs) == 1
    assert jobs[0].failure_stage == "interpretation"
    assert jobs[0].failure_reason == "interpretation_failed_count=1"

    signals = session.scalars(select(PublicationSignal)).all()
    assert len(signals) == 1
    assert signals[0].processing_status == "interpretation_failed"
    assert signals[0].failure_stage == "interpretation"
    assert signals[0].failure_reason == "pdf_text_not_extractable"


def test_duplicate_content_does_not_reprocess_when_contract_version_is_current() -> None:
    session = build_session()
    company = seed_company_and_source(session)
    existing_document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://ri.example.com/docs/previa-1.pdf",
        effective_url="https://ri.example.com/docs/previa-1.pdf",
        content_hash=hashlib.sha256(b"same-pdf-content").hexdigest(),
        file_size_bytes=len(b"same-pdf-content"),
        current_state="canonical",
        contract_version_used="1.0.0",
        normalization_version_used="1.0.0",
    )
    session.add(existing_document)
    session.flush()
    session.add(
        ExtractionRun(
            result_document_id=existing_document.id,
            contract_version="1.0.0",
            llm_provider="openai",
            llm_model="heuristic",
            status="canonicalized",
            raw_contract_payload={},
        )
    )
    session.commit()
    html = """
    <html>
      <body>
        <a href="/docs/previa-1.pdf">Prévia Operacional 1T26</a>
      </body>
    </html>
    """
    semantic_service = StubSemanticProcessingService(
        DocumentSemanticProcessingResult(
            extraction_status="canonicalized",
            document_state="canonical",
            canonical_metric_count=2,
            failed_fact_count=0,
            extraction_run_id=1,
        )
    )
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher({"https://ri.example.com/resultados": html}),
        document_fetcher=StubDocumentFetcher(
            {
                "https://ri.example.com/docs/previa-1.pdf": b"same-pdf-content",
            }
        ),
        semantic_contract_version="1.0.0",
    )
    service.document_semantic_processing_service = semantic_service

    result = service.run_job(scope_type="company", scope_value="mrv")

    assert result.duplicate_document_count == 1
    assert len(semantic_service.calls) == 0


def test_duplicate_content_reprocesses_when_force_reprocess_is_true() -> None:
    session = build_session()
    company = seed_company_and_source(session)
    existing_document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://ri.example.com/docs/previa-1.pdf",
        effective_url="https://ri.example.com/docs/previa-1.pdf",
        content_hash=hashlib.sha256(b"same-pdf-content").hexdigest(),
        file_size_bytes=len(b"same-pdf-content"),
        current_state="canonical",
        contract_version_used="1.0.0",
        normalization_version_used="1.0.0",
    )
    session.add(existing_document)
    session.flush()
    session.add(
        ExtractionRun(
            result_document_id=existing_document.id,
            contract_version="1.0.0",
            llm_provider="openai",
            llm_model="heuristic",
            status="canonicalized",
            raw_contract_payload={},
        )
    )
    session.commit()
    html = """
    <html>
      <body>
        <a href="/docs/previa-1.pdf">Prévia Operacional 1T26</a>
      </body>
    </html>
    """
    semantic_service = StubSemanticProcessingService(
        DocumentSemanticProcessingResult(
            extraction_status="canonicalized",
            document_state="canonical",
            canonical_metric_count=2,
            failed_fact_count=0,
            extraction_run_id=1,
        )
    )
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher({"https://ri.example.com/resultados": html}),
        document_fetcher=StubDocumentFetcher(
            {
                "https://ri.example.com/docs/previa-1.pdf": b"same-pdf-content",
            }
        ),
        semantic_contract_version="1.0.0",
    )
    service.document_semantic_processing_service = semantic_service

    result = service.run_job(scope_type="company", scope_value="mrv", force_reprocess=True)

    assert result.duplicate_document_count == 1
    assert len(semantic_service.calls) == 1


def test_duplicate_content_reprocesses_when_normalization_version_changes() -> None:
    session = build_session()
    company = seed_company_and_source(session)
    existing_document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://ri.example.com/docs/previa-1.pdf",
        effective_url="https://ri.example.com/docs/previa-1.pdf",
        content_hash=hashlib.sha256(b"same-pdf-content").hexdigest(),
        file_size_bytes=len(b"same-pdf-content"),
        current_state="canonical",
        contract_version_used="1.0.0",
        normalization_version_used="0.9.0",
    )
    session.add(existing_document)
    session.flush()
    session.add(
        ExtractionRun(
            result_document_id=existing_document.id,
            contract_version="1.0.0",
            llm_provider="openai",
            llm_model="heuristic",
            status="canonicalized",
            raw_contract_payload={},
        )
    )
    session.commit()
    html = """
    <html>
      <body>
        <a href="/docs/previa-1.pdf">Prévia Operacional 1T26</a>
      </body>
    </html>
    """
    semantic_service = StubSemanticProcessingService(
        DocumentSemanticProcessingResult(
            extraction_status="canonicalized",
            document_state="canonical",
            canonical_metric_count=2,
            failed_fact_count=0,
            extraction_run_id=1,
        )
    )
    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher({"https://ri.example.com/resultados": html}),
        document_fetcher=StubDocumentFetcher(
            {
                "https://ri.example.com/docs/previa-1.pdf": b"same-pdf-content",
            }
        ),
        semantic_contract_version="1.0.0",
    )
    service.document_semantic_processing_service = semantic_service
    service.normalization_knowledge_version = "1.0.0"

    result = service.run_job(scope_type="company", scope_value="mrv")

    assert result.duplicate_document_count == 1
    assert len(semantic_service.calls) == 1
