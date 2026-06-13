from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import Settings
from app.ingestion.jobs import MonitoringJobService


class MonitoringScheduler:
    def __init__(self, settings: Settings, job_service_factory) -> None:
        self.settings = settings
        self.job_service_factory = job_service_factory
        self.scheduler = BackgroundScheduler(timezone="UTC")

    def start(self) -> None:
        if not self.settings.polling_enabled:
            return
        self.scheduler.add_job(
            self._run_monitoring_job,
            trigger="interval",
            minutes=self.settings.polling_interval_minutes,
            id="monitoring_job",
            replace_existing=True,
        )
        self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _run_monitoring_job(self) -> None:
        job_service = self.job_service_factory()
        if not isinstance(job_service, MonitoringJobService):
            return
        job_service.create_job(scope_type="all", scope_value=None)
