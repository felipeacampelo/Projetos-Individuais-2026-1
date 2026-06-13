import pytest

from app.domain.document_lifecycle import (
    DocumentState,
    InvalidDocumentStateTransition,
    assert_document_transition_allowed,
)


def test_valid_document_transition() -> None:
    assert_document_transition_allowed(DocumentState.CONTENT_RECOVERED, DocumentState.OBSERVED)


def test_invalid_document_transition_raises() -> None:
    with pytest.raises(InvalidDocumentStateTransition):
        assert_document_transition_allowed(DocumentState.RECOVERY_FAILED, DocumentState.CANONICAL)
