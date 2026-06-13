from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


CandidateMetricCategory = Literal["operacional", "mercado_habitacional", "desconhecida"]
ValueStatus = Literal["reported", "missing"]


class ReferencePeriodContract(BaseModel):
    year: int = Field(ge=1900, le=9999)
    quarter: int = Field(ge=1, le=4)


class DocumentContract(BaseModel):
    source_url: HttpUrl
    document_type: str
    company_reported_name: str | None = None
    reference_period: ReferencePeriodContract


class ComparativeValueContract(BaseModel):
    kind: str
    value: float
    unit: str


class CandidateCutContract(BaseModel):
    dimension_label: str
    value_label: str
    is_material: bool


class EvidenceContract(BaseModel):
    page: int | None = Field(default=None, ge=1)
    section: str | None = None
    snippet: str = Field(min_length=1)


class CandidateFactContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reported_metric_name: str = Field(min_length=1)
    candidate_metric_category: CandidateMetricCategory
    value_status: ValueStatus
    reported_value: float | None = None
    reported_unit: str | None = None
    canonical_numeric_value: float | None = None
    canonical_unit_hint: str | None = None
    comparative_values: list[ComparativeValueContract] = Field(default_factory=list)
    cuts: list[CandidateCutContract] = Field(default_factory=list)
    evidence: EvidenceContract

    def model_post_init(self, __context: object) -> None:
        if self.value_status == "reported":
            if self.reported_value is None:
                raise ValueError("reported_value is required when value_status='reported'")
            if self.reported_unit is None:
                raise ValueError("reported_unit is required when value_status='reported'")
        if self.value_status == "missing" and self.reported_value is not None:
            raise ValueError("reported_value must be null when value_status='missing'")


class WarningContract(BaseModel):
    code: str
    message: str


class SemanticExtractionContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: str
    extraction_id: str
    document: DocumentContract
    facts: list[CandidateFactContract]
    warnings: list[WarningContract] = Field(default_factory=list)
