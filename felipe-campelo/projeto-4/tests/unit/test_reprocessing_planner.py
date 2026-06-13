from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import Company, ReprocessingRequest, ResultDocument
from app.canonization.reprocessing import ReprocessingPlanner
from app.repositories.reprocessing_repository import ReprocessingRepository


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def test_repository_marks_document_eligible_when_normalization_version_changes() -> None:
    document = ResultDocument(
        company_id=1,
        document_type="previa_operacional",
        source_url="https://example.com/doc.pdf",
        effective_url="https://example.com/doc.pdf",
        content_hash="hash-1",
        file_size_bytes=100,
        current_state="canonical",
        contract_version_used="1.0.0",
        normalization_version_used="0.9.0",
    )

    assert ReprocessingRepository.requires_material_reprocessing(
        document=document,
        semantic_contract_version="1.0.0",
        normalization_knowledge_version="1.0.0",
    )


def test_planner_enqueues_only_documents_with_material_version_change() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()

    session.add_all(
        [
            ResultDocument(
                company_id=company.id,
                document_type="previa_operacional",
                source_url="https://example.com/current.pdf",
                effective_url="https://example.com/current.pdf",
                content_hash="hash-current",
                file_size_bytes=100,
                current_state="canonical",
                contract_version_used="1.0.0",
                normalization_version_used="1.0.0",
            ),
            ResultDocument(
                company_id=company.id,
                document_type="previa_operacional",
                source_url="https://example.com/outdated.pdf",
                effective_url="https://example.com/outdated.pdf",
                content_hash="hash-outdated",
                file_size_bytes=100,
                current_state="canonical",
                contract_version_used="1.0.0",
                normalization_version_used="0.9.0",
            ),
        ]
    )
    session.commit()

    get_settings.cache_clear()
    planner = ReprocessingPlanner(session)
    planner.settings = planner.settings.model_copy(update={"normalization_knowledge_version": "1.0.0"})

    created = planner.enqueue_material_change_requests(
        trigger_type="normalization_knowledge_version",
        trigger_version="1.0.0",
    )

    assert created == 1
    requests = session.query(ReprocessingRequest).order_by(ReprocessingRequest.id.asc()).all()
    assert len(requests) == 1
    assert requests[0].trigger_type == "normalization_knowledge_version"
    assert requests[0].trigger_version == "1.0.0"
