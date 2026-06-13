from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.extractions import (
    ExtractionCutItemResponse,
    ExtractionEvidenceItemResponse,
    ExtractionFactItemResponse,
    ExtractionRunDetailResponse,
    ExtractionRunItemResponse,
    ExtractionRunListResponse,
)
from app.repositories.extraction_repository import ExtractionRepository

router = APIRouter(prefix="/api/extracoes", tags=["extracoes"])


@router.get("", response_model=ExtractionRunListResponse)
def list_extraction_runs(
    document_id: int | None = Query(default=None),
    session: Session = Depends(get_database_session),
) -> ExtractionRunListResponse:
    runs = ExtractionRepository(session).list_runs(result_document_id=document_id)
    return ExtractionRunListResponse(
        data=[
            ExtractionRunItemResponse(
                extraction_id=f"extraction_{run.id}",
                document_id=f"doc_{run.result_document_id}",
                contract_version=run.contract_version,
                llm_provider=run.llm_provider,
                llm_model=run.llm_model,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
            )
            for run in runs
        ]
    )


@router.get("/{extraction_id}", response_model=ExtractionRunDetailResponse)
def get_extraction_run(
    extraction_id: int,
    session: Session = Depends(get_database_session),
) -> ExtractionRunDetailResponse:
    run = ExtractionRepository(session).get_run_detail(extraction_id)
    if run is None:
        raise HTTPException(status_code=404, detail="unknown_extraction_run")

    return ExtractionRunDetailResponse(
        extraction_id=f"extraction_{run.id}",
        document_id=f"doc_{run.result_document_id}",
        contract_version=run.contract_version,
        llm_provider=run.llm_provider,
        llm_model=run.llm_model,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        raw_contract_payload=run.raw_contract_payload,
        facts=[
            ExtractionFactItemResponse(
                fact_id=f"fact_{fact.id}",
                reported_metric_name=fact.reported_metric_name,
                candidate_metric_category=fact.candidate_metric_category,
                value_status=fact.value_status,
                reported_value=fact.reported_value,
                reported_unit=fact.reported_unit,
                canonical_numeric_value=fact.canonical_numeric_value,
                canonical_unit_hint=fact.canonical_unit_hint,
                warnings=fact.warnings_json or [],
                cuts=[
                    ExtractionCutItemResponse(
                        dimension_label=cut.dimension_label,
                        value_label=cut.value_label,
                        is_material=cut.is_material,
                    )
                    for cut in fact.cuts
                ],
                evidence_items=[
                    ExtractionEvidenceItemResponse(
                        page=evidence.page_number,
                        section=evidence.section_label,
                        snippet=evidence.snippet,
                    )
                    for evidence in fact.evidence_items
                ],
            )
            for fact in run.candidate_facts
        ],
    )
