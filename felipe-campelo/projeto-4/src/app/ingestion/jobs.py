from __future__ import annotations

from sqlalchemy.orm import Session

from app.ingestion.signal_discovery.html_discovery import discover_pdf_signals_from_html
from app.ingestion.source_registry import SourceRegistry
from app.repositories.monitoring_repository import MonitoringRepository


class MonitoringJobService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.monitoring_repository = MonitoringRepository(session)
        self.source_registry = SourceRegistry(session)

    def create_job(self, scope_type: str, scope_value: str | None = None) -> int:
        job = self.monitoring_repository.create_job(scope_type=scope_type, scope_value=scope_value)
        self.session.commit()
        return job.id

    def register_discovered_signals_from_html(
        self,
        *,
        company_id: int,
        publication_source_id: int,
        base_url: str,
        html: str,
        job_id: int,
    ) -> int:
        signals = discover_pdf_signals_from_html(html=html, base_url=base_url)
        for signal in signals:
            self.monitoring_repository.add_signal(
                job_id=job_id,
                company_id=company_id,
                publication_source_id=publication_source_id,
                signal_url=signal.signal_url,
                signal_title=signal.signal_title,
            )
        self.session.commit()
        return len(signals)
