from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MonitoringJob, PublicationSignal


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

    def update_signal_status(self, *, signal_id: int, processing_status: str) -> PublicationSignal | None:
        signal = self.get_signal(signal_id)
        if signal is None:
            return None
        signal.processing_status = processing_status
        self.session.add(signal)
        self.session.flush()
        return signal
