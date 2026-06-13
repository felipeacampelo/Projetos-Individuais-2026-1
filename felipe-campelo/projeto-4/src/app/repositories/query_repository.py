from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    CanonicalMetric,
    CanonicalMetricCut,
    Company,
    CompanyAlias,
    DocumentVersion,
    MetricCatalogItem,
    ResultDocument,
)


class QueryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def resolve_company(self, company_ref: str) -> Company | None:
        normalized = company_ref.strip().lower()
        stmt = (
            select(Company)
            .outerjoin(CompanyAlias, CompanyAlias.company_id == Company.id)
            .where(
                Company.is_active.is_(True),
                (Company.slug == normalized)
                | (Company.display_name.ilike(normalized))
                | (CompanyAlias.alias.ilike(normalized))
            )
            .limit(1)
        )
        return self.session.scalar(stmt)

    def resolve_metric_catalog_item(self, metric_ref: str) -> MetricCatalogItem | None:
        normalized = metric_ref.strip().lower()
        stmt = select(MetricCatalogItem).where(
            MetricCatalogItem.is_active.is_(True),
            (MetricCatalogItem.slug == normalized) | (MetricCatalogItem.name.ilike(normalized)),
        )
        return self.session.scalar(stmt.limit(1))

    def list_canonical_metrics(
        self,
        *,
        company_id: int,
        year: int,
        quarter: int,
        metric_catalog_item_id: int | None = None,
    ) -> list[CanonicalMetric]:
        stmt: Select[tuple[CanonicalMetric]] = (
            select(CanonicalMetric)
            .options(
                joinedload(CanonicalMetric.cuts),
                joinedload(CanonicalMetric.metric_catalog_item),
            )
            .where(
                CanonicalMetric.company_id == company_id,
                CanonicalMetric.reference_year == year,
                CanonicalMetric.reference_quarter == quarter,
            )
            .order_by(CanonicalMetric.id.asc())
        )
        if metric_catalog_item_id is not None:
            stmt = stmt.where(CanonicalMetric.metric_catalog_item_id == metric_catalog_item_id)
        return list(self.session.scalars(stmt).unique())

    def list_metric_cuts(self, canonical_metric_id: int) -> list[CanonicalMetricCut]:
        stmt = select(CanonicalMetricCut).where(CanonicalMetricCut.canonical_metric_id == canonical_metric_id)
        return list(self.session.scalars(stmt))

    def get_canonical_document_for_scope(
        self,
        *,
        company_id: int,
        year: int,
        quarter: int,
    ) -> ResultDocument | None:
        stmt = (
            select(ResultDocument)
            .options(joinedload(ResultDocument.company))
            .join(CanonicalMetric, CanonicalMetric.result_document_id == ResultDocument.id)
            .where(
                CanonicalMetric.company_id == company_id,
                CanonicalMetric.reference_year == year,
                CanonicalMetric.reference_quarter == quarter,
            )
            .limit(1)
        )
        return self.session.scalar(stmt)

    def list_documents(
        self,
        *,
        company_id: int | None = None,
        status: str | None = None,
        canonical_only: bool = False,
    ) -> list[ResultDocument]:
        stmt = (
            select(ResultDocument)
            .options(
                joinedload(ResultDocument.company),
                joinedload(ResultDocument.version_entry).joinedload(DocumentVersion.version_group),
            )
            .order_by(ResultDocument.id.asc())
        )
        if company_id is not None:
            stmt = stmt.where(ResultDocument.company_id == company_id)
        if status is not None:
            stmt = stmt.where(ResultDocument.current_state == status)
        if canonical_only:
            stmt = stmt.where(ResultDocument.current_state == "canonical")
        return list(self.session.scalars(stmt))
