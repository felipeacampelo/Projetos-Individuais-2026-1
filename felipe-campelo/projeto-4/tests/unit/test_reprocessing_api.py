from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Company, ReprocessingRequest, ResultDocument
from app.api.routers.reprocessing import get_reprocessing_request, list_reprocessing_requests


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def test_list_reprocessing_requests_returns_document_context() -> None:
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
        contract_version_used="1.0.0",
        normalization_version_used="1.0.0",
    )
    session.add(document)
    session.flush()
    session.add(
        ReprocessingRequest(
            result_document_id=document.id,
            trigger_type="normalization_knowledge_version",
            trigger_version="1.0.0",
            status="pending",
        )
    )
    session.commit()

    response = list_reprocessing_requests(session)

    assert len(response.data) == 1
    item = response.data[0]
    assert item.request_id == "reprocess_1"
    assert item.document_id == "doc_1"
    assert item.company_slug == "mrv"
    assert item.trigger_type == "normalization_knowledge_version"
    assert item.status == "pending"


def test_get_reprocessing_request_returns_processing_versions() -> None:
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
        contract_version_used="1.0.0",
        normalization_version_used="1.0.0",
    )
    session.add(document)
    session.flush()
    request = ReprocessingRequest(
        result_document_id=document.id,
        trigger_type="semantic_contract_version",
        trigger_version="2.0.0",
        status="completed",
    )
    session.add(request)
    session.commit()

    response = get_reprocessing_request(request.id, session)

    assert response.request_id == "reprocess_1"
    assert response.document_id == "doc_1"
    assert response.company_slug == "mrv"
    assert response.source_url == "https://example.com/doc.pdf"
    assert response.document_status == "canonical"
    assert response.contract_version_used == "1.0.0"
    assert response.normalization_version_used == "1.0.0"
