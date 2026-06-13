from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ConjunturaQueryResponse(BaseModel):
    empresa: str
    ano: int
    trimestre: int
    metrica: str | None = None
    dimensao_recorte: str | None = None
    valor_recorte: str | None = None


class ReferencePeriodResponse(BaseModel):
    year: int
    quarter: int


class CanonicalDocumentResponse(BaseModel):
    document_id: str
    document_type: str | None = None
    source_url: str
    published_at: datetime | None = None


class CoverageResponse(BaseModel):
    status: str
    company_slug: str
    reference_period: ReferencePeriodResponse
    canonical_document: CanonicalDocumentResponse | None = None
    reason: str | None = None


class CanonicalMetricCutResponse(BaseModel):
    dimension: str
    value: str


class EvidenceResponse(BaseModel):
    page: int | None = None
    section: str | None = None
    snippet: str | None = None


class CanonicalMetricResponse(BaseModel):
    metric_slug: str
    metric_name: str
    value: float | None = None
    value_status: str
    canonical_unit: str
    reported_unit: str | None = None
    reported_value: float | None = None
    cuts: list[CanonicalMetricCutResponse]
    evidence: EvidenceResponse


class ConjunturaMetaResponse(BaseModel):
    returned_metrics: int
    generated_at: datetime


class ConjunturaResponse(BaseModel):
    query: ConjunturaQueryResponse
    coverage: CoverageResponse
    data: list[CanonicalMetricResponse]
    meta: ConjunturaMetaResponse
