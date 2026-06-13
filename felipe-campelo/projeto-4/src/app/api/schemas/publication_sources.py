from __future__ import annotations

from pydantic import BaseModel


class PublicationSourceItemResponse(BaseModel):
    source_id: str
    company_slug: str
    name: str
    source_type: str
    url: str
    priority: int
    is_active: bool


class PublicationSourceListResponse(BaseModel):
    data: list[PublicationSourceItemResponse]
