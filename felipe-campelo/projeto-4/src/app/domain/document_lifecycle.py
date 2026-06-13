from __future__ import annotations

from enum import StrEnum


class DocumentState(StrEnum):
    SIGNAL_DETECTED = "signal_detected"
    RECOVERY_FAILED = "recovery_failed"
    CONTENT_RECOVERED = "content_recovered"
    DUPLICATE_CONTENT = "duplicate_content"
    OBSERVED = "observed"
    INTERPRETATION_FAILED = "interpretation_failed"
    EXTRACTED = "extracted"
    CANONICALIZATION_FAILED = "canonicalization_failed"
    CANONICAL = "canonical"
    SUPERSEDED = "superseded"


ALLOWED_DOCUMENT_TRANSITIONS: dict[DocumentState, set[DocumentState]] = {
    DocumentState.SIGNAL_DETECTED: {
        DocumentState.CONTENT_RECOVERED,
        DocumentState.RECOVERY_FAILED,
    },
    DocumentState.RECOVERY_FAILED: {
        DocumentState.SIGNAL_DETECTED,
    },
    DocumentState.CONTENT_RECOVERED: {
        DocumentState.DUPLICATE_CONTENT,
        DocumentState.OBSERVED,
    },
    DocumentState.DUPLICATE_CONTENT: set(),
    DocumentState.OBSERVED: {
        DocumentState.EXTRACTED,
        DocumentState.INTERPRETATION_FAILED,
    },
    DocumentState.INTERPRETATION_FAILED: {
        DocumentState.OBSERVED,
    },
    DocumentState.EXTRACTED: {
        DocumentState.CANONICAL,
        DocumentState.CANONICALIZATION_FAILED,
    },
    DocumentState.CANONICALIZATION_FAILED: {
        DocumentState.EXTRACTED,
    },
    DocumentState.CANONICAL: {
        DocumentState.SUPERSEDED,
    },
    DocumentState.SUPERSEDED: set(),
}


class InvalidDocumentStateTransition(ValueError):
    """Raised when a document lifecycle transition is not allowed."""


def assert_document_transition_allowed(current: DocumentState, new: DocumentState) -> None:
    allowed = ALLOWED_DOCUMENT_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise InvalidDocumentStateTransition(
            f"Invalid document state transition: {current.value} -> {new.value}"
        )
