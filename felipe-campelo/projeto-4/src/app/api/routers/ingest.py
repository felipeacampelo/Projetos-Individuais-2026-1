from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.ingest import IngestRequest, IngestRequestedScopeResponse, IngestResponse
from app.ingestion.jobs import MonitoringJobService

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


@router.post("/run", response_model=IngestResponse)
def run_ingest(
    request: IngestRequest,
    session: Session = Depends(get_database_session),
) -> IngestResponse:
    job_service = MonitoringJobService(session)
    scope_type = "company" if request.company_slug else "all"
    try:
        result = job_service.run_job(
            scope_type=scope_type,
            scope_value=request.company_slug,
            force_reprocess=request.force_reprocess,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return IngestResponse(
        job_id=f"job_{result.job_id}",
        status=result.status,
        requested_scope=IngestRequestedScopeResponse(
            company_slug=request.company_slug,
            force_reprocess=request.force_reprocess,
        ),
    )
