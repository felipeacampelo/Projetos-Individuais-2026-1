from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.extraction.service import DocumentSemanticProcessingService
from app.ingestion.document_recovery import DocumentRecoveryService
from app.ingestion.fetchers.document_fetcher import DocumentFetcher
from app.ingestion.fetchers.results_page_fetcher import ResultsPageFetchError, ResultsPageFetcher
from app.ingestion.signal_discovery.html_discovery import discover_pdf_signals_from_html
from app.observability.logging import LogContext, StructuredLogger
from app.repositories.company_repository import CompanyRepository
from app.ingestion.source_registry import SourceRegistry
from app.repositories.monitoring_repository import MonitoringRepository


@dataclass(frozen=True)
class MonitoringRunResult:
    job_id: int
    status: str
    discovered_signal_count: int
    recovered_document_count: int
    duplicate_document_count: int
    recovery_failed_count: int
    source_error_count: int
    extracted_document_count: int
    canonical_document_count: int


class MonitoringJobService:
    def __init__(
        self,
        session: Session,
        *,
        results_page_fetcher: ResultsPageFetcher | None = None,
        document_fetcher: DocumentFetcher | None = None,
    ) -> None:
        self.session = session
        self.company_repository = CompanyRepository(session)
        self.monitoring_repository = MonitoringRepository(session)
        self.source_registry = SourceRegistry(session)
        self.results_page_fetcher = results_page_fetcher or ResultsPageFetcher()
        self.document_recovery_service = DocumentRecoveryService(session, fetcher=document_fetcher)
        self.document_semantic_processing_service = DocumentSemanticProcessingService(session)
        self.logger = StructuredLogger("pipeline_uda.monitoring")

    def close(self) -> None:
        self.session.close()

    def create_job(self, scope_type: str, scope_value: str | None = None) -> int:
        job = self.monitoring_repository.create_job(scope_type=scope_type, scope_value=scope_value)
        self.session.commit()
        self.logger.info(
            "monitoring_job_started",
            LogContext(job_id=f"job_{job.id}", extra={"scope_type": scope_type, "scope_value": scope_value}),
        )
        return job.id

    def run_job(
        self,
        *,
        scope_type: str,
        scope_value: str | None = None,
        force_reprocess: bool = False,
    ) -> MonitoringRunResult:
        del force_reprocess

        job = self.monitoring_repository.create_job(scope_type=scope_type, scope_value=scope_value)
        self.session.commit()

        discovered_signal_count = 0
        recovered_document_count = 0
        duplicate_document_count = 0
        recovery_failed_count = 0
        source_error_count = 0
        extracted_document_count = 0
        canonical_document_count = 0
        interpretation_failed_count = 0
        canonicalization_failed_count = 0
        source_failure_reasons: list[str] = []

        try:
            sources = self._resolve_sources(scope_type=scope_type, scope_value=scope_value)

            for source in sources:
                try:
                    html = self.results_page_fetcher.fetch_html(source.url)
                except ResultsPageFetchError as exc:
                    source_error_count += 1
                    source_failure_reasons.append(f"{source.url}: {exc}")
                    self.logger.error(
                        "results_page_fetch_failed",
                        LogContext(
                            job_id=f"job_{job.id}",
                            extra={
                                "publication_source_url": source.url,
                                "failure_stage": "source_fetch",
                                "failure_reason": str(exc),
                            },
                        ),
                    )
                    continue

                signals = discover_pdf_signals_from_html(html=html, base_url=source.url)
                discovered_signal_count += len(signals)
                self.logger.info(
                    "publication_signals_discovered",
                    LogContext(
                        job_id=f"job_{job.id}",
                        extra={
                            "publication_source_url": source.url,
                            "signal_count": len(signals),
                        },
                    ),
                )

                for signal in signals:
                    persisted_signal = self.monitoring_repository.add_signal(
                        job_id=job.id,
                        company_id=source.company_id,
                        publication_source_id=source.source_id,
                        signal_url=signal.signal_url,
                        signal_title=signal.signal_title,
                    )
                    self.session.commit()
                    signal_context = LogContext(
                        job_id=f"job_{job.id}",
                        signal_id=f"signal_{persisted_signal.id}",
                        extra={"signal_url": signal.signal_url},
                    )
                    self.logger.info("publication_signal_registered", signal_context)

                    recovery_result = self.document_recovery_service.recover_from_signal(
                        signal_id=persisted_signal.id,
                        company_id=source.company_id,
                        signal_url=signal.signal_url,
                        document_type=self._infer_document_type(signal.signal_title),
                    )
                    if recovery_result.status == "observed":
                        recovered_document_count += 1
                        self.logger.info(
                            "document_content_recovered",
                            LogContext(
                                job_id=f"job_{job.id}",
                                signal_id=f"signal_{persisted_signal.id}",
                                document_id=f"doc_{recovery_result.result_document_id}",
                                extra={
                                    "content_hash": recovery_result.content_hash,
                                    "effective_url": recovery_result.effective_url,
                                },
                            ),
                        )
                        if recovery_result.result_document_id is not None and recovery_result.content is not None:
                            semantic_result = self.document_semantic_processing_service.process_document(
                                result_document_id=recovery_result.result_document_id,
                                content=recovery_result.content,
                                source_url=signal.signal_url,
                                document_type=self._infer_document_type(signal.signal_title) or "documento_resultado",
                            )
                            semantic_context = LogContext(
                                job_id=f"job_{job.id}",
                                signal_id=f"signal_{persisted_signal.id}",
                                document_id=f"doc_{recovery_result.result_document_id}",
                                extraction_id=(
                                    f"extraction_{semantic_result.extraction_run_id}"
                                    if semantic_result.extraction_run_id is not None
                                    else None
                                ),
                                extra={
                                    "processing_status": semantic_result.extraction_status,
                                    "document_state": semantic_result.document_state,
                                    "failure_stage": semantic_result.failure_stage,
                                    "failure_reason": semantic_result.failure_reason,
                                },
                            )
                            if semantic_result.extraction_status in {"extracted", "canonicalized"}:
                                extracted_document_count += 1
                            if semantic_result.document_state == "canonical":
                                canonical_document_count += 1
                            if semantic_result.failure_stage is not None:
                                if semantic_result.failure_stage == "interpretation":
                                    interpretation_failed_count += 1
                                elif semantic_result.failure_stage == "canonicalization":
                                    canonicalization_failed_count += 1
                                self.monitoring_repository.update_signal_processing(
                                    signal_id=persisted_signal.id,
                                    processing_status=semantic_result.document_state,
                                    failure_stage=semantic_result.failure_stage,
                                    failure_reason=semantic_result.failure_reason,
                                )
                                self.session.commit()
                                self.logger.error("document_semantic_processing_failed", semantic_context)
                            else:
                                self.logger.info("document_semantic_processing_completed", semantic_context)
                    elif recovery_result.status == "duplicate_content":
                        duplicate_document_count += 1
                        self.logger.info("document_duplicate_detected", signal_context)
                    elif recovery_result.status == "recovery_failed":
                        recovery_failed_count += 1
                        self.logger.error(
                            "document_recovery_failed",
                            LogContext(
                                job_id=f"job_{job.id}",
                                signal_id=f"signal_{persisted_signal.id}",
                                extra={
                                    "failure_stage": recovery_result.failure_stage,
                                    "failure_reason": recovery_result.failure_reason,
                                },
                            ),
                        )

            final_status = self._resolve_job_status(
                discovered_signal_count=discovered_signal_count,
                recovered_document_count=recovered_document_count,
                duplicate_document_count=duplicate_document_count,
                recovery_failed_count=recovery_failed_count,
                source_error_count=source_error_count,
                extracted_document_count=extracted_document_count,
                canonical_document_count=canonical_document_count,
            )
            job_failure_reason = self._build_job_failure_reason(
                source_failure_reasons=source_failure_reasons,
                recovery_failed_count=recovery_failed_count,
                interpretation_failed_count=interpretation_failed_count,
                canonicalization_failed_count=canonicalization_failed_count,
            )
            self.monitoring_repository.update_job_status(
                job_id=job.id,
                status=final_status,
                failure_stage=self._build_job_failure_stage(
                    source_error_count=source_error_count,
                    recovery_failed_count=recovery_failed_count,
                    interpretation_failed_count=interpretation_failed_count,
                    canonicalization_failed_count=canonicalization_failed_count,
                ),
                failure_reason=job_failure_reason,
                mark_finished=True,
            )
            self.session.commit()
            self.logger.info(
                "monitoring_job_finished",
                LogContext(
                    job_id=f"job_{job.id}",
                    extra={
                        "status": final_status,
                        "discovered_signal_count": discovered_signal_count,
                        "recovered_document_count": recovered_document_count,
                        "duplicate_document_count": duplicate_document_count,
                        "recovery_failed_count": recovery_failed_count,
                        "source_error_count": source_error_count,
                        "extracted_document_count": extracted_document_count,
                        "canonical_document_count": canonical_document_count,
                        "interpretation_failed_count": interpretation_failed_count,
                        "canonicalization_failed_count": canonicalization_failed_count,
                    },
                ),
            )
            return MonitoringRunResult(
                job_id=job.id,
                status=final_status,
                discovered_signal_count=discovered_signal_count,
                recovered_document_count=recovered_document_count,
                duplicate_document_count=duplicate_document_count,
                recovery_failed_count=recovery_failed_count,
                source_error_count=source_error_count,
                extracted_document_count=extracted_document_count,
                canonical_document_count=canonical_document_count,
            )
        except Exception as exc:
            self.session.rollback()
            self.monitoring_repository.update_job_status(
                job_id=job.id,
                status="failed",
                failure_stage="job_runtime",
                failure_reason=str(exc),
                error_message=str(exc),
                mark_finished=True,
            )
            self.session.commit()
            self.logger.error(
                "monitoring_job_failed",
                LogContext(
                    job_id=f"job_{job.id}",
                    extra={"failure_stage": "job_runtime", "failure_reason": str(exc)},
                ),
            )
            raise

    def register_discovered_signals_from_html(
        self,
        *,
        company_id: int,
        publication_source_id: int,
        base_url: str,
        html: str,
        job_id: int,
    ) -> int:
        signals = discover_pdf_signals_from_html(html=html, base_url=base_url)
        for signal in signals:
            self.monitoring_repository.add_signal(
                job_id=job_id,
                company_id=company_id,
                publication_source_id=publication_source_id,
                signal_url=signal.signal_url,
                signal_title=signal.signal_title,
            )
        self.session.commit()
        return len(signals)

    def _resolve_sources(self, *, scope_type: str, scope_value: str | None) -> list:
        if scope_type == "company":
            if not scope_value:
                raise ValueError("company scope requires company_slug")
            company = self.company_repository.resolve_active(scope_value)
            if company is None:
                raise ValueError(f"unknown company: {scope_value}")
            return self.source_registry.list_active_sources(company_id=company.id)
        return self.source_registry.list_active_sources()

    @staticmethod
    def _resolve_job_status(
        *,
        discovered_signal_count: int,
        recovered_document_count: int,
        duplicate_document_count: int,
        recovery_failed_count: int,
        source_error_count: int,
        extracted_document_count: int,
        canonical_document_count: int,
    ) -> str:
        successful_work = (
            discovered_signal_count
            + recovered_document_count
            + duplicate_document_count
            + extracted_document_count
            + canonical_document_count
        )
        if source_error_count and not successful_work and not recovery_failed_count:
            return "failed"
        if source_error_count or recovery_failed_count:
            return "completed_with_errors"
        return "completed"

    @staticmethod
    def _infer_document_type(signal_title: str | None) -> str | None:
        if not signal_title:
            return None
        normalized = signal_title.strip().lower()
        if "prévia operacional" in normalized or "previa operacional" in normalized:
            return "previa_operacional"
        if "resultado" in normalized or "release" in normalized:
            return "documento_resultado"
        return None

    @staticmethod
    def _build_job_failure_stage(
        *,
        source_error_count: int,
        recovery_failed_count: int,
        interpretation_failed_count: int,
        canonicalization_failed_count: int,
    ) -> str | None:
        if source_error_count:
            return "source_fetch"
        if recovery_failed_count:
            return "recovery"
        if interpretation_failed_count:
            return "interpretation"
        if canonicalization_failed_count:
            return "canonicalization"
        return None

    @staticmethod
    def _build_job_failure_reason(
        *,
        source_failure_reasons: list[str],
        recovery_failed_count: int,
        interpretation_failed_count: int,
        canonicalization_failed_count: int,
    ) -> str | None:
        parts: list[str] = []
        if source_failure_reasons:
            parts.append("source_fetch=" + " | ".join(source_failure_reasons))
        if recovery_failed_count:
            parts.append(f"recovery_failed_count={recovery_failed_count}")
        if interpretation_failed_count:
            parts.append(f"interpretation_failed_count={interpretation_failed_count}")
        if canonicalization_failed_count:
            parts.append(f"canonicalization_failed_count={canonicalization_failed_count}")
        return "; ".join(parts) or None
