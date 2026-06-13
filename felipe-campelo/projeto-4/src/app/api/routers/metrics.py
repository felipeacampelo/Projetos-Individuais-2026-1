from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_database_session
from app.api.schemas.metric_catalog import MetricCatalogItemResponse, MetricCatalogListResponse
from app.repositories.metric_catalog_repository import MetricCatalogRepository

router = APIRouter(prefix="/api/metricas", tags=["metricas"])


@router.get("", response_model=MetricCatalogListResponse)
def list_metrics(
    q: str | None = Query(default=None),
    session: Session = Depends(get_database_session),
) -> MetricCatalogListResponse:
    items = MetricCatalogRepository(session).list_active(query=q)
    data = [
        MetricCatalogItemResponse(
            slug=item.slug,
            name=item.name,
            category=item.category,
            canonical_unit=item.canonical_unit,
        )
        for item in items
    ]
    return MetricCatalogListResponse(data=data)
