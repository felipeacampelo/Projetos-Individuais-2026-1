from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResultDocument(Base):
    __tablename__ = "result_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str] = mapped_column(String(2048))
    effective_url: Mapped[str] = mapped_column(String(2048))
    content_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_state: Mapped[str] = mapped_column(String(50))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    discovery_links: Mapped[list["DocumentDiscoveryLink"]] = relationship(
        back_populates="result_document",
        cascade="all, delete-orphan",
    )
    company: Mapped["Company | None"] = relationship()


class DocumentDiscoveryLink(Base):
    __tablename__ = "document_discovery_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_document_id: Mapped[int] = mapped_column(
        ForeignKey("result_documents.id", ondelete="CASCADE")
    )
    publication_signal_id: Mapped[int] = mapped_column(
        ForeignKey("publication_signals.id", ondelete="CASCADE")
    )
    link_type: Mapped[str] = mapped_column(String(50), default="discovered_from")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    result_document: Mapped[ResultDocument] = relationship(back_populates="discovery_links")
    publication_signal: Mapped["PublicationSignal"] = relationship()
