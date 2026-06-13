from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExtractionRun(Base):
    __tablename__ = "extraction_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_document_id: Mapped[int] = mapped_column(
        ForeignKey("result_documents.id", ondelete="CASCADE")
    )
    contract_version: Mapped[str] = mapped_column(String(50))
    llm_provider: Mapped[str] = mapped_column(String(100))
    llm_model: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_contract_payload: Mapped[dict] = mapped_column(JSON)

    candidate_facts: Mapped[list["CandidateFact"]] = relationship(
        back_populates="extraction_run",
        cascade="all, delete-orphan",
    )


class CandidateFact(Base):
    __tablename__ = "candidate_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    extraction_run_id: Mapped[int] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="CASCADE")
    )
    reported_metric_name: Mapped[str] = mapped_column(String(255))
    candidate_metric_category: Mapped[str] = mapped_column(String(100))
    value_status: Mapped[str] = mapped_column(String(50))
    reported_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    reported_unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    canonical_numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    canonical_unit_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    warnings_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    extraction_run: Mapped[ExtractionRun] = relationship(back_populates="candidate_facts")
    cuts: Mapped[list["CandidateFactCut"]] = relationship(
        back_populates="candidate_fact",
        cascade="all, delete-orphan",
    )
    evidence_items: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="candidate_fact",
        cascade="all, delete-orphan",
    )


class CandidateFactCut(Base):
    __tablename__ = "candidate_fact_cuts"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_fact_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_facts.id", ondelete="CASCADE")
    )
    dimension_label: Mapped[str] = mapped_column(String(100))
    value_label: Mapped[str] = mapped_column(String(255))
    is_material: Mapped[bool] = mapped_column(Boolean, nullable=False)

    candidate_fact: Mapped[CandidateFact] = relationship(back_populates="cuts")


class ExtractionEvidence(Base):
    __tablename__ = "extraction_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_fact_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_facts.id", ondelete="CASCADE")
    )
    page_number: Mapped[int | None] = mapped_column(nullable=True)
    section_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snippet: Mapped[str] = mapped_column(Text)

    candidate_fact: Mapped[CandidateFact] = relationship(back_populates="evidence_items")
