from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import MetricCatalogAlias, MetricCatalogItem


@dataclass(frozen=True)
class NormalizedMetricResult:
    metric_catalog_item: MetricCatalogItem


class MetricNormalizer:
    def __init__(self, session: Session) -> None:
        self.session = session

    def normalize(self, reported_metric_name: str) -> NormalizedMetricResult | None:
        normalized = reported_metric_name.strip().lower()
        stmt = (
            select(MetricCatalogItem)
            .outerjoin(MetricCatalogAlias, MetricCatalogAlias.metric_catalog_item_id == MetricCatalogItem.id)
            .where(
                MetricCatalogItem.is_active.is_(True),
                or_(
                    func.lower(MetricCatalogItem.slug) == normalized,
                    func.lower(MetricCatalogItem.name) == normalized,
                    func.lower(MetricCatalogAlias.alias) == normalized,
                ),
            )
            .limit(1)
        )
        item = self.session.scalar(stmt)
        if item is None:
            return None
        return NormalizedMetricResult(metric_catalog_item=item)
