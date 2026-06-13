from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NormalizationKnowledgeVersion(Base):
    __tablename__ = "normalization_knowledge_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CanonicalMetric(Base):
    __tablename__ = "canonical_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    result_document_id: Mapped[int] = mapped_column(
        ForeignKey("result_documents.id", ondelete="CASCADE")
    )
    metric_catalog_item_id: Mapped[int] = mapped_column(
        ForeignKey("metric_catalog_items.id", ondelete="CASCADE")
    )
    reference_year: Mapped[int] = mapped_column()
    reference_quarter: Mapped[int] = mapped_column()
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_status: Mapped[str] = mapped_column(String(50))
    canonical_unit: Mapped[str] = mapped_column(String(50))
    reported_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    reported_unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coverage_status: Mapped[str] = mapped_column(String(50), default="available")

    cuts: Mapped[list["CanonicalMetricCut"]] = relationship(
        back_populates="canonical_metric",
        cascade="all, delete-orphan",
    )
    metric_catalog_item: Mapped["MetricCatalogItem"] = relationship()
    result_document: Mapped["ResultDocument"] = relationship()


class CanonicalMetricCut(Base):
    __tablename__ = "canonical_metric_cuts"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_metric_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_metrics.id", ondelete="CASCADE")
    )
    dimension: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(255))

    canonical_metric: Mapped[CanonicalMetric] = relationship(back_populates="cuts")
