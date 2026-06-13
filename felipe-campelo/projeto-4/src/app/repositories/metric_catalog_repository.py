from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import MetricCatalogItem


class MetricCatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_active(self, query: str | None = None) -> list[MetricCatalogItem]:
        stmt = (
            select(MetricCatalogItem)
            .where(MetricCatalogItem.is_active.is_(True))
            .options(selectinload(MetricCatalogItem.aliases))
            .order_by(MetricCatalogItem.slug.asc())
        )
        if query:
            normalized = f"%{query.strip().lower()}%"
            stmt = stmt.where(MetricCatalogItem.slug.ilike(normalized) | MetricCatalogItem.name.ilike(normalized))
        return list(self.session.scalars(stmt))
