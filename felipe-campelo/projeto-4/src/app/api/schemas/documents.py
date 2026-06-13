from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DocumentReferencePeriodResponse(BaseModel):
    year: int | None = None
    quarter: int | None = None


class DocumentItemResponse(BaseModel):
    document_id: str
    company_slug: str | None = None
    reference_period: DocumentReferencePeriodResponse
    version_number: int | None = None
    document_type: str | None = None
    status: str
    source_url: str
    content_hash: str
    published_at: datetime | None = None
    is_canonical: bool


class DocumentListResponse(BaseModel):
    data: list[DocumentItemResponse]


class DocumentLineageSignalResponse(BaseModel):
    signal_id: str
    publication_source_id: str | None = None
    publication_source_name: str | None = None
    signal_url: str
    signal_title: str | None = None
    discovered_at: datetime | None = None
    processing_status: str | None = None


class DocumentLineageResponse(BaseModel):
    document_id: str
    company_slug: str | None = None
    reference_period: DocumentReferencePeriodResponse | None = None
    version_number: int | None = None
    source_url: str
    effective_url: str
    content_hash: str
    status: str
    lineage_signals: list[DocumentLineageSignalResponse]
