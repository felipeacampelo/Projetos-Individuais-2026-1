from __future__ import annotations

from enum import StrEnum


class RecoveryFailureReason(StrEnum):
    EMPTY_RESPONSE = "empty_response"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    HTTP_ERROR = "http_error"
    UNKNOWN = "unknown"


class InterpretationFailureReason(StrEnum):
    PDF_PARSE_ERROR = "pdf_parse_error"
    EMPTY_TEXT = "empty_text"
    INVALID_CONTRACT = "invalid_contract"
    UNKNOWN = "unknown"


class CanonizationFailureReason(StrEnum):
    COMPANY_NOT_NORMALIZED = "company_not_normalized"
    METRIC_NOT_NORMALIZED = "metric_not_normalized"
    UNIT_NOT_NORMALIZED = "unit_not_normalized"
    CUT_NOT_NORMALIZED = "cut_not_normalized"
    MEANING_CHANGE_BLOCKED = "meaning_change_blocked"
    SEMANTIC_COMPLETENESS_FAILED = "semantic_completeness_failed"
    UNKNOWN = "unknown"
