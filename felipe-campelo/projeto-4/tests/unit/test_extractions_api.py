from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base
from app.db.models import CandidateFact, Company, ExtractionEvidence, ExtractionRun, ResultDocument
from app.api.routers.extractions import get_extraction_run, list_extraction_runs


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    return factory()


def test_list_extraction_runs_filters_by_document() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    document1 = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc1.pdf",
        effective_url="https://example.com/doc1.pdf",
        content_hash="hash-1",
        file_size_bytes=100,
        current_state="canonical",
    )
    document2 = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc2.pdf",
        effective_url="https://example.com/doc2.pdf",
        content_hash="hash-2",
        file_size_bytes=100,
        current_state="canonical",
    )
    session.add_all([document1, document2])
    session.flush()
    session.add_all(
        [
            ExtractionRun(
                result_document_id=document1.id,
                contract_version="1.0.0",
                llm_provider="heuristic",
                llm_model="h1",
                status="canonicalized",
                raw_contract_payload={},
            ),
            ExtractionRun(
                result_document_id=document2.id,
                contract_version="1.0.0",
                llm_provider="heuristic",
                llm_model="h1",
                status="canonicalized",
                raw_contract_payload={},
            ),
        ]
    )
    session.commit()

    response = list_extraction_runs(document_id=document1.id, session=session)

    assert len(response.data) == 1
    assert response.data[0].document_id == "doc_1"


def test_get_extraction_run_returns_facts_and_evidence() -> None:
    session = build_session()
    company = Company(slug="mrv", display_name="MRV")
    session.add(company)
    session.flush()
    document = ResultDocument(
        company_id=company.id,
        document_type="previa_operacional",
        source_url="https://example.com/doc1.pdf",
        effective_url="https://example.com/doc1.pdf",
        content_hash="hash-1",
        file_size_bytes=100,
        current_state="canonical",
    )
    session.add(document)
    session.flush()
    run = ExtractionRun(
        result_document_id=document.id,
        contract_version="1.0.0",
        llm_provider="heuristic",
        llm_model="h1",
        status="canonicalized",
        raw_contract_payload={"contract_version": "1.0.0"},
    )
    session.add(run)
    session.flush()
    fact = CandidateFact(
        extraction_run_id=run.id,
        reported_metric_name="VSO",
        candidate_metric_category="operacional",
        value_status="reported",
        reported_value=10.0,
        reported_unit="%",
        canonical_numeric_value=10.0,
        canonical_unit_hint="percentage",
        warnings_json=[{"code": "x", "message": "y"}],
    )
    session.add(fact)
    session.flush()
    session.add(
        ExtractionEvidence(
            candidate_fact_id=fact.id,
            page_number=1,
            section_label="Destaques",
            snippet="VSO 10,0%",
        )
    )
    session.commit()

    response = get_extraction_run(run.id, session=session)

    assert response.extraction_id == "extraction_1"
    assert response.document_id == "doc_1"
    assert response.raw_contract_payload["contract_version"] == "1.0.0"
    assert len(response.facts) == 1
    assert response.facts[0].reported_metric_name == "VSO"
    assert response.facts[0].evidence_items[0].snippet == "VSO 10,0%"
