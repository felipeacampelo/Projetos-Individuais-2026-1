from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MetricCatalogItem(Base):
    __tablename__ = "metric_catalog_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))
    canonical_unit: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    aliases: Mapped[list["MetricCatalogAlias"]] = relationship(
        back_populates="metric_catalog_item",
        cascade="all, delete-orphan",
    )


class MetricCatalogAlias(Base):
    __tablename__ = "metric_catalog_aliases"
    __table_args__ = (
        UniqueConstraint("metric_catalog_item_id", "alias", name="uq_metric_catalog_alias"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_catalog_item_id: Mapped[int] = mapped_column(
        ForeignKey("metric_catalog_items.id", ondelete="CASCADE")
    )
    alias: Mapped[str] = mapped_column(String(255), index=True)

    metric_catalog_item: Mapped[MetricCatalogItem] = relationship(back_populates="aliases")
