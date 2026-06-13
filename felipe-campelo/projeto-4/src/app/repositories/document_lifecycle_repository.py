from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import ResultDocument
from app.domain.document_lifecycle import (
    DocumentState,
    InvalidDocumentStateTransition,
    assert_document_transition_allowed,
)


class DocumentLifecycleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def transition_state(self, document: ResultDocument, new_state: DocumentState) -> ResultDocument:
        current_state = DocumentState(document.current_state)
        assert_document_transition_allowed(current_state, new_state)
        document.current_state = new_state.value
        self.session.add(document)
        self.session.flush()
        return document

    def force_state(self, document: ResultDocument, new_state: DocumentState) -> ResultDocument:
        document.current_state = new_state.value
        self.session.add(document)
        self.session.flush()
        return document
