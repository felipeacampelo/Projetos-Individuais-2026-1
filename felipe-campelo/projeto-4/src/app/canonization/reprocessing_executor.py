from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.extraction.service import DocumentSemanticProcessingService
from app.ingestion.fetchers.document_fetcher import DocumentFetchError, DocumentFetcher
from app.observability.logging import LogContext, StructuredLogger
from app.repositories.reprocessing_repository import ReprocessingRepository
from app.repositories.result_document_repository import ResultDocumentRepository


@dataclass(frozen=True)
class ReprocessingExecutionResult:
    processed_count: int
    completed_count: int
    failed_count: int


class ReprocessingExecutor:
    def __init__(
        self,
        session: Session,
        *,
        fetcher: DocumentFetcher | None = None,
    ) -> None:
        self.session = session
        self.fetcher = fetcher or DocumentFetcher()
        self.reprocessing_repository = ReprocessingRepository(session)
        self.result_document_repository = ResultDocumentRepository(session)
        self.semantic_processing_service = DocumentSemanticProcessingService(session)
        self.logger = StructuredLogger("pipeline_uda.reprocessing")

    def close(self) -> None:
        self.session.close()

    def execute_pending(self) -> ReprocessingExecutionResult:
        pending = self.reprocessing_repository.list_pending()
        processed_count = 0
        completed_count = 0
        failed_count = 0

        for request in pending:
            processed_count += 1
            document = self.result_document_repository.get_by_id(request.result_document_id)
            if document is None:
                self.reprocessing_repository.mark_failed(request, "unknown_result_document")
                self.session.commit()
                failed_count += 1
                continue

            self.reprocessing_repository.mark_processing(request)
            self.session.commit()

            context = LogContext(
                document_id=f"doc_{document.id}",
                extra={
                    "reprocessing_request_id": request.id,
                    "trigger_type": request.trigger_type,
                    "trigger_version": request.trigger_version,
                },
            )
            self.logger.info("reprocessing_request_started", context)

            try:
                fetched = self.fetcher.fetch(document.effective_url or document.source_url)
                result = self.semantic_processing_service.process_document(
                    result_document_id=document.id,
                    content=fetched.content,
                    source_url=fetched.effective_url,
                    document_type=document.document_type or "documento_resultado_trimestral",
                )
                if result.failure_stage is not None:
                    self.reprocessing_repository.mark_failed(
                        request,
                        f"{result.failure_stage}:{result.failure_reason}",
                    )
                    self.session.commit()
                    failed_count += 1
                    self.logger.error("reprocessing_request_failed", context)
                    continue

                self.reprocessing_repository.mark_completed(request)
                self.session.commit()
                completed_count += 1
                self.logger.info("reprocessing_request_completed", context)
            except DocumentFetchError as exc:
                self.reprocessing_repository.mark_failed(request, str(exc))
                self.session.commit()
                failed_count += 1
                self.logger.error("reprocessing_request_failed", context)
            except Exception as exc:
                self.reprocessing_repository.mark_failed(request, str(exc))
                self.session.commit()
                failed_count += 1
                self.logger.error("reprocessing_request_failed", context)

        return ReprocessingExecutionResult(
            processed_count=processed_count,
            completed_count=completed_count,
            failed_count=failed_count,
        )
