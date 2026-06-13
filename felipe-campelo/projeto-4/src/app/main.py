from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers.companies import router as companies_router
from app.api.routers.conjuntura import router as conjuntura_router
from app.api.routers.documents import router as documents_router
from app.api.routers.health import router as health_router
from app.api.routers.ingest import router as ingest_router
from app.api.routers.metrics import router as metrics_router
from app.api.routers.monitoring import router as monitoring_router
from app.api.routers.publication_sources import router as publication_sources_router
from app.api.routers.reprocessing import router as reprocessing_router
from app.canonization.reprocessing_executor import ReprocessingExecutor
from app.config import get_settings
from app.db.session import SessionLocal
from app.ingestion.jobs import MonitoringJobService
from app.ingestion.scheduler import MonitoringScheduler


def _build_monitoring_job_service() -> MonitoringJobService:
    session = SessionLocal()
    return MonitoringJobService(session)


def _build_reprocessing_executor() -> ReprocessingExecutor:
    session = SessionLocal()
    return ReprocessingExecutor(session)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    scheduler = MonitoringScheduler(settings, _build_monitoring_job_service, _build_reprocessing_executor)
    scheduler.start()
    app.state.monitoring_scheduler = scheduler
    try:
        yield
    finally:
        scheduler.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(companies_router)
    app.include_router(conjuntura_router)
    app.include_router(documents_router)
    app.include_router(publication_sources_router)
    app.include_router(monitoring_router)
    app.include_router(reprocessing_router)
    app.include_router(ingest_router)
    app.include_router(metrics_router)
    return app


app = create_app()
