from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import CanonicalMetric, Company, MetricCatalogItem, ResultDocument
from app.canonization.canonical_source_service import ReevaluateCanonicalSourceService
from app.repositories.canonical_metric_repository import CanonicalMetricRepository


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def test_new_higher_precedence_document_supersedes_previous_canonical() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    metric_catalog = MetricCatalogItem(
        slug="vso",
        name="VSO",
        category="operacional_comercial",
        canonical_unit="percentage",
        is_active=True,
    )
    session.add_all([company, metric_catalog])
    session.flush()

    old_document = ResultDocument(
        company_id=company.id,
        document_type="documento_resultado_trimestral",
        source_url="https://example.com/release.pdf",
        effective_url="https://example.com/release.pdf",
        content_hash="old-hash",
        file_size_bytes=100,
        current_state="canonical",
    )
    new_document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/previa.pdf",
        effective_url="https://example.com/previa.pdf",
        content_hash="new-hash",
        file_size_bytes=100,
        current_state="canonical",
    )
    session.add_all([old_document, new_document])
    session.flush()

    repository = CanonicalMetricRepository(session)
    repository.create_metric(
        company_id=company.id,
        result_document_id=old_document.id,
        metric_catalog_item_id=metric_catalog.id,
        reference_year=2026,
        reference_quarter=1,
        value=10.0,
        value_status="reported",
        canonical_unit="percentage",
        reported_value=10.0,
        reported_unit="%",
    )
    repository.create_metric(
        company_id=company.id,
        result_document_id=new_document.id,
        metric_catalog_item_id=metric_catalog.id,
        reference_year=2026,
        reference_quarter=1,
        value=12.0,
        value_status="reported",
        canonical_unit="percentage",
        reported_value=12.0,
        reported_unit="%",
    )
    session.commit()

    decision = ReevaluateCanonicalSourceService(session).reevaluate_scope(
        company_id=company.id,
        reference_year=2026,
        reference_quarter=1,
    )

    assert decision is not None
    assert decision.winning_document_id == new_document.id
    assert old_document.id in decision.superseded_document_ids
    assert decision.deleted_metric_count == 1

    refreshed_old = session.get(ResultDocument, old_document.id)
    refreshed_new = session.get(ResultDocument, new_document.id)
    assert refreshed_old is not None and refreshed_old.current_state == "superseded"
    assert refreshed_new is not None and refreshed_new.current_state == "canonical"

    remaining_metrics = session.query(CanonicalMetric).order_by(CanonicalMetric.id.asc()).all()
    assert len(remaining_metrics) == 1
    assert remaining_metrics[0].result_document_id == new_document.id
