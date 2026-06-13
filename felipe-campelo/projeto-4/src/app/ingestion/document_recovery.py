from __future__ import annotations

import hashlib
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.domain.document_lifecycle import DocumentState
from app.repositories.document_lifecycle_repository import DocumentLifecycleRepository
from app.ingestion.fetchers.document_fetcher import DocumentFetchError, DocumentFetcher, FetchedDocument
from app.repositories.monitoring_repository import MonitoringRepository
from app.repositories.result_document_repository import ResultDocumentRepository


@dataclass(frozen=True)
class DocumentRecoveryResult:
    status: str
    result_document_id: int | None
    content_hash: str | None
    effective_url: str | None
    file_size_bytes: int | None


class DocumentRecoveryService:
    def __init__(self, session: Session, fetcher: DocumentFetcher | None = None) -> None:
        self.session = session
        self.fetcher = fetcher or DocumentFetcher()
        self.result_document_repository = ResultDocumentRepository(session)
        self.document_lifecycle_repository = DocumentLifecycleRepository(session)
        self.monitoring_repository = MonitoringRepository(session)

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def recover_from_signal(
        self,
        *,
        signal_id: int,
        company_id: int,
        signal_url: str,
        document_type: str | None = None,
    ) -> DocumentRecoveryResult:
        try:
            fetched = self.fetcher.fetch(signal_url)
        except DocumentFetchError:
            self.monitoring_repository.update_signal_status(signal_id=signal_id, processing_status="recovery_failed")
            self.session.commit()
            return DocumentRecoveryResult(
                status="recovery_failed",
                result_document_id=None,
                content_hash=None,
                effective_url=None,
                file_size_bytes=None,
            )

        return self._persist_fetched_document(
            signal_id=signal_id,
            company_id=company_id,
            document_type=document_type,
            fetched=fetched,
        )

    def _persist_fetched_document(
        self,
        *,
        signal_id: int,
        company_id: int,
        document_type: str | None,
        fetched: FetchedDocument,
    ) -> DocumentRecoveryResult:
        content_hash = self.compute_sha256(fetched.content)
        file_size_bytes = len(fetched.content)

        existing = self.result_document_repository.get_by_content_hash(content_hash)
        if existing is not None:
            self.result_document_repository.refresh_last_seen(existing)
            self.result_document_repository.add_discovery_link(
                result_document_id=existing.id,
                publication_signal_id=signal_id,
            )
            self.monitoring_repository.update_signal_status(signal_id=signal_id, processing_status="duplicate_content")
            self.session.commit()
            return DocumentRecoveryResult(
                status="duplicate_content",
                result_document_id=existing.id,
                content_hash=content_hash,
                effective_url=fetched.effective_url,
                file_size_bytes=file_size_bytes,
            )

        document = self.result_document_repository.create(
            company_id=company_id,
            document_type=document_type,
            source_url=fetched.source_url,
            effective_url=fetched.effective_url,
            content_hash=content_hash,
            file_size_bytes=file_size_bytes,
            current_state=DocumentState.CONTENT_RECOVERED.value,
        )
        self.document_lifecycle_repository.transition_state(document, DocumentState.OBSERVED)
        self.result_document_repository.add_discovery_link(
            result_document_id=document.id,
            publication_signal_id=signal_id,
        )
        self.monitoring_repository.update_signal_status(signal_id=signal_id, processing_status="content_recovered")
        self.session.commit()
        return DocumentRecoveryResult(
            status="observed",
            result_document_id=document.id,
            content_hash=content_hash,
            effective_url=fetched.effective_url,
            file_size_bytes=file_size_bytes,
        )
