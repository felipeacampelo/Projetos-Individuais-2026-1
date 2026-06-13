from __future__ import annotations

from pydantic import BaseModel


class MetricCatalogItemResponse(BaseModel):
    slug: str
    name: str
    category: str
    canonical_unit: str


class MetricCatalogListResponse(BaseModel):
    data: list[MetricCatalogItemResponse]
