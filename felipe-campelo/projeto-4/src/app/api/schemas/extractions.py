from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ExtractionEvidenceItemResponse(BaseModel):
    page: int | None = None
    section: str | None = None
    snippet: str


class ExtractionCutItemResponse(BaseModel):
    dimension_label: str
    value_label: str
    is_material: bool


class ExtractionFactItemResponse(BaseModel):
    fact_id: str
    reported_metric_name: str
    candidate_metric_category: str
    value_status: str
    reported_value: float | None = None
    reported_unit: str | None = None
    canonical_numeric_value: float | None = None
    canonical_unit_hint: str | None = None
    warnings: list[dict] = []
    cuts: list[ExtractionCutItemResponse]
    evidence_items: list[ExtractionEvidenceItemResponse]


class ExtractionRunItemResponse(BaseModel):
    extraction_id: str
    document_id: str
    contract_version: str
    llm_provider: str
    llm_model: str
    status: str
    started_at: datetime
    finished_at: datetime | None = None


class ExtractionRunListResponse(BaseModel):
    data: list[ExtractionRunItemResponse]


class ExtractionRunDetailResponse(ExtractionRunItemResponse):
    raw_contract_payload: dict
    facts: list[ExtractionFactItemResponse]
