from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReprocessingRequest(Base):
    __tablename__ = "reprocessing_requests"
    __table_args__ = (
        UniqueConstraint(
            "result_document_id",
            "trigger_type",
            "trigger_version",
            name="uq_reprocessing_request_trigger",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    result_document_id: Mapped[int] = mapped_column(
        ForeignKey("result_documents.id", ondelete="CASCADE")
    )
    trigger_type: Mapped[str] = mapped_column(String(100))
    trigger_version: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    result_document: Mapped["ResultDocument"] = relationship()
