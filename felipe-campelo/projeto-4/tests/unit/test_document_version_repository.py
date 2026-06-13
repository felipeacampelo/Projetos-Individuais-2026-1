from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Company, ResultDocument
from app.repositories.document_version_repository import DocumentVersionRepository


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def test_assigns_incremental_versions_within_same_company_period() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    doc1 = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc1.pdf",
        effective_url="https://example.com/doc1.pdf",
        content_hash="hash-1",
        file_size_bytes=100,
        current_state="observed",
    )
    doc2 = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc2.pdf",
        effective_url="https://example.com/doc2.pdf",
        content_hash="hash-2",
        file_size_bytes=100,
        current_state="observed",
    )
    session.add_all([doc1, doc2])
    session.commit()

    repository = DocumentVersionRepository(session)
    version1 = repository.ensure_document_version(
        result_document_id=doc1.id,
        company_id=company.id,
        reference_year=2026,
        reference_quarter=1,
    )
    version2 = repository.ensure_document_version(
        result_document_id=doc2.id,
        company_id=company.id,
        reference_year=2026,
        reference_quarter=1,
    )

    assert version1.version_number == 1
    assert version2.version_number == 2
    assert version1.version_group_id == version2.version_group_id
