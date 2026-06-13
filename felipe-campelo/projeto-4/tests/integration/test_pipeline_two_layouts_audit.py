from __future__ import annotations

from pathlib import Path

import fitz
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import (
    CanonicalMetric,
    Company,
    CompanyAlias,
    DocumentDiscoveryLink,
    DocumentVersion,
    ExtractionEvidence,
    ExtractionRun,
    MetricCatalogAlias,
    MetricCatalogItem,
    PublicationSource,
    PublicationSignal,
    ResultDocument,
)
from app.ingestion.fetchers.document_fetcher import FetchedDocument
from app.ingestion.jobs import MonitoringJobService


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class StubResultsPageFetcher:
    def __init__(self, html_by_url: dict[str, str]) -> None:
        self.html_by_url = html_by_url

    def fetch_html(self, url: str) -> str:
        return self.html_by_url[url]


class StubDocumentFetcher:
    def __init__(self, payloads_by_url: dict[str, bytes]) -> None:
        self.payloads_by_url = payloads_by_url

    def fetch(self, url: str) -> FetchedDocument:
        return FetchedDocument(
            source_url=url,
            effective_url=url,
            content=self.payloads_by_url[url],
            content_type="application/pdf",
        )


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


def read_fixture(name: str) -> str:
    return (FIXTURES_DIR / "html" / name).read_text()


def seed_company_source_and_metric_catalog(session: Session) -> Company:
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    session.add_all(
        [
            CompanyAlias(company_id=company.id, alias="mrv", alias_type="display_name"),
            CompanyAlias(company_id=company.id, alias="mrv&co", alias_type="ri_name"),
            PublicationSource(
                company_id=company.id,
                name="Central de Resultados MRV",
                source_type="results_page",
                url="https://ri.example.com/resultados/mrv",
                priority=10,
                is_active=True,
            ),
        ]
    )

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
    return company


def test_pipeline_processes_two_layouts_with_full_audit_trail_and_single_canonical_source() -> None:
    session = build_session()
    company = seed_company_source_and_metric_catalog(session)
    html = read_fixture("results-page-mrv.html")

    service = MonitoringJobService(
        session,
        results_page_fetcher=StubResultsPageFetcher({"https://ri.example.com/resultados/mrv": html}),
        document_fetcher=StubDocumentFetcher(
            {
                "https://ri.example.com/mrv/previa-operacional-3t25.pdf": build_pdf_bytes(
                    [
                        "MRV 3T25 Prévia Operacional",
                        "VSO 11,4%",
                        "Vendas Líquidas R$ 410 milhões",
                    ]
                ),
                "https://ri.example.com/mrv/apresentacao-resultados-3t25.pdf": build_pdf_bytes(
                    [
                        "MRV&CO 3T25 Apresentação de Resultados",
                        "VSO",
                        "10,8%",
                        "Vendas Líquidas",
                        "R$ 405 milhões",
                    ]
                ),
            }
        ),
    )

    result = service.run_job(scope_type="company", scope_value=company.slug)

    assert result.status == "completed"
    assert result.discovered_signal_count == 2
    assert result.recovered_document_count == 2
    assert result.extracted_document_count == 2

    signals = session.scalars(select(PublicationSignal).order_by(PublicationSignal.id.asc())).all()
    assert len(signals) == 2
    assert all(signal.processing_status == "content_recovered" for signal in signals)
    assert all(signal.failure_stage is None for signal in signals)

    documents = session.scalars(select(ResultDocument).order_by(ResultDocument.id.asc())).all()
    assert len(documents) == 2
    assert [document.document_type for document in documents] == [
        "previa_operacional",
        "apresentacao_resultados",
    ]
    assert [document.current_state for document in documents] == [
        "canonical",
        "superseded",
    ]

    discovery_links = session.scalars(select(DocumentDiscoveryLink).order_by(DocumentDiscoveryLink.id.asc())).all()
    assert len(discovery_links) == 2
    assert {link.result_document_id for link in discovery_links} == {document.id for document in documents}

    extraction_runs = session.scalars(select(ExtractionRun).order_by(ExtractionRun.id.asc())).all()
    assert len(extraction_runs) == 2
    assert all(run.status == "canonicalized" for run in extraction_runs)

    evidence_items = session.scalars(select(ExtractionEvidence).order_by(ExtractionEvidence.id.asc())).all()
    assert len(evidence_items) >= 4

    versions = session.scalars(select(DocumentVersion).order_by(DocumentVersion.version_number.asc())).all()
    assert len(versions) == 2
    assert [version.version_number for version in versions] == [1, 2]

    canonical_metrics = session.scalars(select(CanonicalMetric).order_by(CanonicalMetric.id.asc())).all()
    assert len(canonical_metrics) == 2
    assert all(metric.result_document_id == documents[0].id for metric in canonical_metrics)
    assert all(metric.company_id == company.id for metric in canonical_metrics)
    assert all(metric.reference_year == 2025 and metric.reference_quarter == 3 for metric in canonical_metrics)
