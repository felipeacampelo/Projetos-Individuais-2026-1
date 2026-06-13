from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import MonitoringJob, PublicationSignal


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MonitoringRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(self, scope_type: str, scope_value: str | None, status: str = "running") -> MonitoringJob:
        job = MonitoringJob(
            scope_type=scope_type,
            scope_value=scope_value,
            status=status,
        )
        self.session.add(job)
        self.session.flush()
        return job

    def add_signal(
        self,
        *,
        job_id: int,
        company_id: int,
        publication_source_id: int,
        signal_url: str,
        signal_title: str | None,
        processing_status: str = "signal_detected",
    ) -> PublicationSignal:
        signal = PublicationSignal(
            job_id=job_id,
            company_id=company_id,
            publication_source_id=publication_source_id,
            signal_url=signal_url,
            signal_title=signal_title,
            processing_status=processing_status,
        )
        self.session.add(signal)
        self.session.flush()
        return signal

    def get_signal(self, signal_id: int) -> PublicationSignal | None:
        return self.session.scalar(select(PublicationSignal).where(PublicationSignal.id == signal_id))

    def get_job(self, job_id: int) -> MonitoringJob | None:
        stmt = (
            select(MonitoringJob)
            .where(MonitoringJob.id == job_id)
            .options(joinedload(MonitoringJob.publication_signals))
        )
        return self.session.scalar(stmt)

    def list_jobs(self) -> list[MonitoringJob]:
        stmt = (
            select(MonitoringJob)
            .options(joinedload(MonitoringJob.publication_signals))
            .order_by(MonitoringJob.id.desc())
        )
        return list(self.session.scalars(stmt).unique())

    def list_job_signals(self, job_id: int) -> list[PublicationSignal]:
        stmt = (
            select(PublicationSignal)
            .where(PublicationSignal.job_id == job_id)
            .options(
                joinedload(PublicationSignal.company),
                joinedload(PublicationSignal.publication_source),
            )
            .order_by(PublicationSignal.id.asc())
        )
        return list(self.session.scalars(stmt))

    def update_signal_status(self, *, signal_id: int, processing_status: str) -> PublicationSignal | None:
        signal = self.get_signal(signal_id)
        if signal is None:
            return None
        signal.processing_status = processing_status
        self.session.add(signal)
        self.session.flush()
        return signal

    def update_job_status(
        self,
        *,
        job_id: int,
        status: str,
        error_message: str | None = None,
        mark_finished: bool = False,
    ) -> MonitoringJob | None:
        job = self.get_job(job_id)
        if job is None:
            return None
        job.status = status
        job.error_message = error_message
        if mark_finished:
            job.finished_at = utc_now()
        self.session.add(job)
        self.session.flush()
        return job
