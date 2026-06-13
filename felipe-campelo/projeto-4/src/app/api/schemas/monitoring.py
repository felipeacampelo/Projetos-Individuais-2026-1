from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MonitoringSignalItemResponse(BaseModel):
    signal_id: str
    company_slug: str | None = None
    publication_source_id: str
    signal_url: str
    signal_title: str | None = None
    discovered_at: datetime
    processing_status: str
    failure_stage: str | None = None
    failure_reason: str | None = None


class MonitoringJobItemResponse(BaseModel):
    job_id: str
    scope_type: str
    scope_value: str | None = None
    status: str
    started_at: datetime
    finished_at: datetime | None = None
    failure_stage: str | None = None
    failure_reason: str | None = None
    error_message: str | None = None
    signal_count: int


class MonitoringJobListResponse(BaseModel):
    data: list[MonitoringJobItemResponse]


class MonitoringJobDetailResponse(MonitoringJobItemResponse):
    signals: list[MonitoringSignalItemResponse]
