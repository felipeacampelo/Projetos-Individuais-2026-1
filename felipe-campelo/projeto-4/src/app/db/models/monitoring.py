from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MonitoringJob(Base):
    __tablename__ = "monitoring_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope_type: Mapped[str] = mapped_column(String(50))
    scope_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    publication_signals: Mapped[list["PublicationSignal"]] = relationship(
        back_populates="monitoring_job",
        cascade="all, delete-orphan",
    )


class PublicationSignal(Base):
    __tablename__ = "publication_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("monitoring_jobs.id", ondelete="CASCADE"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    publication_source_id: Mapped[int] = mapped_column(
        ForeignKey("publication_sources.id", ondelete="CASCADE")
    )
    signal_url: Mapped[str] = mapped_column(String(2048))
    signal_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    processing_status: Mapped[str] = mapped_column(String(50), default="signal_detected")
    failure_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    monitoring_job: Mapped[MonitoringJob] = relationship(back_populates="publication_signals")
    company: Mapped["Company"] = relationship()
    publication_source: Mapped["PublicationSource"] = relationship(back_populates="publication_signals")
