from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import CanonicalMetric, CandidateFact, Company, ExtractionEvidence, ExtractionRun, MetricCatalogItem, ResultDocument
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


def test_more_complete_same_priority_document_wins_canonical_source() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    metric_vso = MetricCatalogItem(
        slug="vso",
        name="VSO",
        category="operacional_comercial",
        canonical_unit="percentage",
        is_active=True,
    )
    metric_sales = MetricCatalogItem(
        slug="vendas-liquidas",
        name="Vendas Líquidas",
        category="operacional_comercial",
        canonical_unit="brl",
        is_active=True,
    )
    session.add_all([company, metric_vso, metric_sales])
    session.flush()

    weaker_document = ResultDocument(
        company_id=company.id,
        document_type="documento_resultado_trimestral",
        source_url="https://example.com/release-v1.pdf",
        effective_url="https://example.com/release-v1.pdf",
        content_hash="weak-hash",
        file_size_bytes=100,
        current_state="canonical",
    )
    stronger_document = ResultDocument(
        company_id=company.id,
        document_type="documento_resultado_trimestral",
        source_url="https://example.com/release-v2.pdf",
        effective_url="https://example.com/release-v2.pdf",
        content_hash="strong-hash",
        file_size_bytes=100,
        current_state="canonical",
    )
    session.add_all([weaker_document, stronger_document])
    session.flush()

    weak_run = ExtractionRun(
        result_document_id=weaker_document.id,
        contract_version="1.0.0",
        llm_provider="heuristic",
        llm_model="h1",
        status="canonicalized",
        raw_contract_payload={},
    )
    strong_run = ExtractionRun(
        result_document_id=stronger_document.id,
        contract_version="1.0.0",
        llm_provider="heuristic",
        llm_model="h1",
        status="canonicalized",
        raw_contract_payload={},
    )
    session.add_all([weak_run, strong_run])
    session.flush()

    weak_fact = CandidateFact(
        extraction_run_id=weak_run.id,
        reported_metric_name="VSO",
        candidate_metric_category="operacional",
        value_status="reported",
        reported_value=10.0,
        reported_unit="%",
        canonical_numeric_value=10.0,
        canonical_unit_hint="percentage",
        warnings_json=[],
    )
    strong_fact_1 = CandidateFact(
        extraction_run_id=strong_run.id,
        reported_metric_name="VSO",
        candidate_metric_category="operacional",
        value_status="reported",
        reported_value=12.0,
        reported_unit="%",
        canonical_numeric_value=12.0,
        canonical_unit_hint="percentage",
        warnings_json=[],
    )
    strong_fact_2 = CandidateFact(
        extraction_run_id=strong_run.id,
        reported_metric_name="Vendas Líquidas",
        candidate_metric_category="operacional",
        value_status="reported",
        reported_value=420.0,
        reported_unit="R$ milhões",
        canonical_numeric_value=420.0,
        canonical_unit_hint="brl",
        warnings_json=[],
    )
    session.add_all([weak_fact, strong_fact_1, strong_fact_2])
    session.flush()
    session.add_all(
        [
            ExtractionEvidence(candidate_fact_id=weak_fact.id, page_number=1, section_label="Resumo", snippet="VSO 10,0%"),
            ExtractionEvidence(candidate_fact_id=strong_fact_1.id, page_number=1, section_label="Resumo", snippet="VSO 12,0%"),
            ExtractionEvidence(candidate_fact_id=strong_fact_2.id, page_number=2, section_label="Resumo", snippet="Vendas Líquidas R$ 420 milhões"),
        ]
    )

    repository = CanonicalMetricRepository(session)
    repository.create_metric(
        company_id=company.id,
        result_document_id=weaker_document.id,
        metric_catalog_item_id=metric_vso.id,
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
        result_document_id=stronger_document.id,
        metric_catalog_item_id=metric_vso.id,
        reference_year=2026,
        reference_quarter=1,
        value=12.0,
        value_status="reported",
        canonical_unit="percentage",
        reported_value=12.0,
        reported_unit="%",
    )
    repository.create_metric(
        company_id=company.id,
        result_document_id=stronger_document.id,
        metric_catalog_item_id=metric_sales.id,
        reference_year=2026,
        reference_quarter=1,
        value=420.0,
        value_status="reported",
        canonical_unit="brl",
        reported_value=420.0,
        reported_unit="R$ milhões",
    )
    session.commit()

    decision = ReevaluateCanonicalSourceService(session).reevaluate_scope(
        company_id=company.id,
        reference_year=2026,
        reference_quarter=1,
    )

    assert decision is not None
    assert decision.winning_document_id == stronger_document.id
    assert weaker_document.id in decision.superseded_document_ids
    assert decision.winning_completeness_score is not None
    assert decision.winning_completeness_score > 0
