from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint
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
    contract_version_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    normalization_version_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    discovery_links: Mapped[list["DocumentDiscoveryLink"]] = relationship(
        back_populates="result_document",
        cascade="all, delete-orphan",
    )
    company: Mapped["Company | None"] = relationship()
    version_entry: Mapped["DocumentVersion | None"] = relationship(back_populates="result_document")


class DocumentVersionGroup(Base):
    __tablename__ = "document_version_groups"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "reference_year",
            "reference_quarter",
            name="uq_document_version_group_company_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"))
    reference_year: Mapped[int] = mapped_column()
    reference_quarter: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship()
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="version_group",
        cascade="all, delete-orphan",
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("result_document_id", name="uq_document_version_result_document"),
        UniqueConstraint("version_group_id", "version_number", name="uq_document_version_group_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    version_group_id: Mapped[int] = mapped_column(
        ForeignKey("document_version_groups.id", ondelete="CASCADE")
    )
    result_document_id: Mapped[int] = mapped_column(
        ForeignKey("result_documents.id", ondelete="CASCADE")
    )
    version_number: Mapped[int] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    version_group: Mapped[DocumentVersionGroup] = relationship(back_populates="versions")
    result_document: Mapped[ResultDocument] = relationship(back_populates="version_entry")


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
