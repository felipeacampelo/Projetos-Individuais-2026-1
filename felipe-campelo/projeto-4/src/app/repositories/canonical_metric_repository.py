from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import CanonicalMetric, CanonicalMetricCut


class CanonicalMetricRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_metric(
        self,
        *,
        company_id: int,
        result_document_id: int,
        metric_catalog_item_id: int,
        reference_year: int,
        reference_quarter: int,
        value: float | None,
        value_status: str,
        canonical_unit: str,
        reported_value: float | None,
        reported_unit: str | None,
        coverage_status: str = "available",
    ) -> CanonicalMetric:
        metric = CanonicalMetric(
            company_id=company_id,
            result_document_id=result_document_id,
            metric_catalog_item_id=metric_catalog_item_id,
            reference_year=reference_year,
            reference_quarter=reference_quarter,
            value=value,
            value_status=value_status,
            canonical_unit=canonical_unit,
            reported_value=reported_value,
            reported_unit=reported_unit,
            coverage_status=coverage_status,
        )
        self.session.add(metric)
        self.session.flush()
        return metric

    def add_cut(self, *, canonical_metric_id: int, dimension: str, value: str) -> CanonicalMetricCut:
        cut = CanonicalMetricCut(
            canonical_metric_id=canonical_metric_id,
            dimension=dimension,
            value=value,
        )
        self.session.add(cut)
        self.session.flush()
        return cut

    def list_for_document(self, result_document_id: int) -> list[CanonicalMetric]:
        stmt = select(CanonicalMetric).where(CanonicalMetric.result_document_id == result_document_id)
        return list(self.session.scalars(stmt))

    def list_for_scope(
        self,
        *,
        company_id: int,
        reference_year: int,
        reference_quarter: int,
    ) -> list[CanonicalMetric]:
        stmt = select(CanonicalMetric).where(
            CanonicalMetric.company_id == company_id,
            CanonicalMetric.reference_year == reference_year,
            CanonicalMetric.reference_quarter == reference_quarter,
        )
        return list(self.session.scalars(stmt))

    def delete_for_document(self, result_document_id: int) -> None:
        self.session.execute(
            delete(CanonicalMetric).where(CanonicalMetric.result_document_id == result_document_id)
        )
        self.session.flush()
