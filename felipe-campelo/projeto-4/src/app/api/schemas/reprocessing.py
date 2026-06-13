from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReprocessingRequestItemResponse(BaseModel):
    request_id: str
    document_id: str
    company_slug: str | None = None
    trigger_type: str
    trigger_version: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


class ReprocessingRequestListResponse(BaseModel):
    data: list[ReprocessingRequestItemResponse]


class ReprocessingRequestDetailResponse(ReprocessingRequestItemResponse):
    source_url: str | None = None
    effective_url: str | None = None
    document_status: str | None = None
    contract_version_used: str | None = None
    normalization_version_used: str | None = None
