from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentDiscoveryLink, ResultDocument
from app.domain.document_lifecycle import DocumentState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResultDocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_content_hash(self, content_hash: str) -> ResultDocument | None:
        stmt = select(ResultDocument).where(ResultDocument.content_hash == content_hash)
        return self.session.scalar(stmt)

    def create(
        self,
        *,
        company_id: int | None,
        document_type: str | None,
        source_url: str,
        effective_url: str,
        content_hash: str,
        file_size_bytes: int,
        current_state: str = "observed",
    ) -> ResultDocument:
        document = ResultDocument(
            company_id=company_id,
            document_type=document_type,
            source_url=source_url,
            effective_url=effective_url,
            content_hash=content_hash,
            file_size_bytes=file_size_bytes,
            current_state=current_state,
        )
        self.session.add(document)
        self.session.flush()
        return document

    def get_by_id(self, document_id: int) -> ResultDocument | None:
        return self.session.get(ResultDocument, document_id)

    def mark_last_seen_and_state(
        self,
        document: ResultDocument,
        *,
        state: DocumentState | None = None,
    ) -> ResultDocument:
        document.last_seen_at = utc_now()
        if state is not None:
            document.current_state = state.value
        self.session.add(document)
        self.session.flush()
        return document

    def refresh_last_seen(self, document: ResultDocument) -> ResultDocument:
        document.last_seen_at = utc_now()
        self.session.add(document)
        self.session.flush()
        return document

    def add_discovery_link(
        self,
        *,
        result_document_id: int,
        publication_signal_id: int,
        link_type: str = "discovered_from",
        notes: str | None = None,
    ) -> DocumentDiscoveryLink:
        existing = self.session.scalar(
            select(DocumentDiscoveryLink).where(
                DocumentDiscoveryLink.result_document_id == result_document_id,
                DocumentDiscoveryLink.publication_signal_id == publication_signal_id,
            )
        )
        if existing is not None:
            return existing

        link = DocumentDiscoveryLink(
            result_document_id=result_document_id,
            publication_signal_id=publication_signal_id,
            link_type=link_type,
            notes=notes,
        )
        self.session.add(link)
        self.session.flush()
        return link
