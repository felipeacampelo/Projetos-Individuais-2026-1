from __future__ import annotations

from fastapi import APIRouter, Depends
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
    job_id = job_service.create_job(scope_type=scope_type, scope_value=request.company_slug)
    return IngestResponse(
        job_id=f"job_{job_id}",
        status="accepted",
        requested_scope=IngestRequestedScopeResponse(
            company_slug=request.company_slug,
            force_reprocess=request.force_reprocess,
        ),
    )
