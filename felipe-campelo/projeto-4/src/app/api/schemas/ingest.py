from __future__ import annotations

from pydantic import BaseModel


class IngestRequest(BaseModel):
    company_slug: str | None = None
    force_reprocess: bool = False


class IngestRequestedScopeResponse(BaseModel):
    company_slug: str | None = None
    force_reprocess: bool


class IngestResponse(BaseModel):
    job_id: str
    status: str
    requested_scope: IngestRequestedScopeResponse
