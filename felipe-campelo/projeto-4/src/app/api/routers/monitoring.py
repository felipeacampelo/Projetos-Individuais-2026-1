from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.monitoring import (
    MonitoringJobDetailResponse,
    MonitoringJobItemResponse,
    MonitoringJobListResponse,
    MonitoringSignalItemResponse,
)
from app.repositories.monitoring_repository import MonitoringRepository

router = APIRouter(prefix="/api/monitoramentos", tags=["monitoramentos"])


@router.get("", response_model=MonitoringJobListResponse)
def list_monitoring_jobs(session: Session = Depends(get_database_session)) -> MonitoringJobListResponse:
    jobs = MonitoringRepository(session).list_jobs()
    return MonitoringJobListResponse(
        data=[
            MonitoringJobItemResponse(
                job_id=f"job_{job.id}",
                scope_type=job.scope_type,
                scope_value=job.scope_value,
                status=job.status,
                started_at=job.started_at,
                finished_at=job.finished_at,
                error_message=job.error_message,
                signal_count=len(job.publication_signals),
            )
            for job in jobs
        ]
    )


@router.get("/{job_id}", response_model=MonitoringJobDetailResponse)
def get_monitoring_job(job_id: int, session: Session = Depends(get_database_session)) -> MonitoringJobDetailResponse:
    repository = MonitoringRepository(session)
    job = repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown_job")
    signals = repository.list_job_signals(job.id)
    return MonitoringJobDetailResponse(
        job_id=f"job_{job.id}",
        scope_type=job.scope_type,
        scope_value=job.scope_value,
        status=job.status,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_message=job.error_message,
        signal_count=len(signals),
        signals=[
            MonitoringSignalItemResponse(
                signal_id=f"signal_{signal.id}",
                company_slug=signal.company.slug if signal.company else None,
                publication_source_id=f"source_{signal.publication_source_id}",
                signal_url=signal.signal_url,
                signal_title=signal.signal_title,
                discovered_at=signal.discovered_at,
                processing_status=signal.processing_status,
            )
            for signal in signals
        ],
    )
