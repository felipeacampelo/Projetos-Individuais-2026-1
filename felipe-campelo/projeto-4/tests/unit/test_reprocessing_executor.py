from __future__ import annotations

import fitz
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Company, ReprocessingRequest, ResultDocument
from app.canonization.reprocessing_executor import ReprocessingExecutor
from app.extraction.service import DocumentSemanticProcessingResult
from app.ingestion.fetchers.document_fetcher import DocumentFetchError, FetchedDocument


class StubDocumentFetcher:
    def __init__(self, payloads_by_url: dict[str, bytes], failing_urls: set[str] | None = None) -> None:
        self.payloads_by_url = payloads_by_url
        self.failing_urls = failing_urls or set()

    def fetch(self, url: str) -> FetchedDocument:
        if url in self.failing_urls:
            raise DocumentFetchError("synthetic reprocessing fetch failure")
        return FetchedDocument(
            source_url=url,
            effective_url=url,
            content=self.payloads_by_url[url],
            content_type="application/pdf",
        )


class StubSemanticProcessingService:
    def __init__(self, result: DocumentSemanticProcessingResult) -> None:
        self.result = result
        self.calls = 0

    def process_document(
        self,
        *,
        result_document_id: int,
        content: bytes,
        source_url: str,
        document_type: str,
    ) -> DocumentSemanticProcessingResult:
        del result_document_id, content, source_url, document_type
        self.calls += 1
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


def test_execute_pending_marks_request_completed() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc.pdf",
        effective_url="https://example.com/doc.pdf",
        content_hash="hash-1",
        file_size_bytes=100,
        current_state="canonical",
    )
    session.add(document)
    session.flush()
    request = ReprocessingRequest(
        result_document_id=document.id,
        trigger_type="normalization_knowledge_version",
        trigger_version="1.0.0",
        status="pending",
    )
    session.add(request)
    session.commit()

    executor = ReprocessingExecutor(
        session,
        fetcher=StubDocumentFetcher(
            {"https://example.com/doc.pdf": build_pdf_bytes(["MRV 1T26", "VSO 10,0%"])}
        ),
    )
    executor.semantic_processing_service = StubSemanticProcessingService(
        DocumentSemanticProcessingResult(
            extraction_status="canonicalized",
            document_state="canonical",
            canonical_metric_count=1,
            failed_fact_count=0,
            extraction_run_id=1,
        )
    )

    result = executor.execute_pending()

    assert result.processed_count == 1
    assert result.completed_count == 1
    assert result.failed_count == 0
    refreshed = session.get(ReprocessingRequest, request.id)
    assert refreshed is not None
    assert refreshed.status == "completed"
    assert refreshed.started_at is not None
    assert refreshed.finished_at is not None
    assert refreshed.error_message is None


def test_execute_pending_marks_request_failed_on_fetch_error() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc.pdf",
        effective_url="https://example.com/doc.pdf",
        content_hash="hash-1",
        file_size_bytes=100,
        current_state="canonical",
    )
    session.add(document)
    session.flush()
    request = ReprocessingRequest(
        result_document_id=document.id,
        trigger_type="semantic_contract_version",
        trigger_version="2.0.0",
        status="pending",
    )
    session.add(request)
    session.commit()

    executor = ReprocessingExecutor(
        session,
        fetcher=StubDocumentFetcher({}, failing_urls={"https://example.com/doc.pdf"}),
    )

    result = executor.execute_pending()

    assert result.processed_count == 1
    assert result.completed_count == 0
    assert result.failed_count == 1
    refreshed = session.get(ReprocessingRequest, request.id)
    assert refreshed is not None
    assert refreshed.status == "failed"
    assert refreshed.error_message == "synthetic reprocessing fetch failure"
