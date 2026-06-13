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
    document_type: str | None = None
    status: str
    source_url: str
    content_hash: str
    published_at: datetime | None = None
    is_canonical: bool


class DocumentListResponse(BaseModel):
    data: list[DocumentItemResponse]
