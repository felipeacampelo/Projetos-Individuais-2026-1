from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.canonization.canonical_source_service import ReevaluateCanonicalSourceService
from app.canonization.service import CanonizationService
from app.domain.document_lifecycle import DocumentState
from app.extraction.llm.base import LLMExtractionClient
from app.extraction.llm.factory import build_llm_extraction_client
from app.extraction.pipelines.semantic_extraction import SemanticExtractionPipeline
from app.repositories.document_lifecycle_repository import DocumentLifecycleRepository
from app.repositories.document_version_repository import DocumentVersionRepository
from app.repositories.extraction_repository import ExtractionRepository
from app.repositories.result_document_repository import ResultDocumentRepository


@dataclass(frozen=True)
class DocumentSemanticProcessingResult:
    extraction_status: str
    document_state: str
    canonical_metric_count: int
    failed_fact_count: int
    extraction_run_id: int | None = None
    failure_stage: str | None = None
    failure_reason: str | None = None


class DocumentSemanticProcessingService:
    def __init__(self, session: Session, *, llm_client: LLMExtractionClient | None = None) -> None:
        self.session = session
        self.extraction_pipeline = SemanticExtractionPipeline(
            session=session,
            llm_client=llm_client or build_llm_extraction_client(),
        )
        self.canonical_source_service = ReevaluateCanonicalSourceService(session)
        self.canonization_service = CanonizationService(session)
        self.document_lifecycle_repository = DocumentLifecycleRepository(session)
        self.document_version_repository = DocumentVersionRepository(session)
        self.result_document_repository = ResultDocumentRepository(session)
        self.extraction_repository = ExtractionRepository(session)

    def process_document(
        self,
        *,
        result_document_id: int,
        content: bytes,
        source_url: str,
        document_type: str,
    ) -> DocumentSemanticProcessingResult:
        document = self.result_document_repository.get_by_id(result_document_id)
        if document is None:
            raise ValueError(f"unknown result document: {result_document_id}")

        try:
            contract = self.extraction_pipeline.run(
                result_document_id=result_document_id,
                content=content,
                source_url=source_url,
                document_type=document_type or "documento_resultado",
            )
        except Exception as exc:
            self.document_lifecycle_repository.force_state(document, DocumentState.INTERPRETATION_FAILED)
            self.session.commit()
            return DocumentSemanticProcessingResult(
                extraction_status="interpretation_failed",
                document_state=DocumentState.INTERPRETATION_FAILED.value,
                canonical_metric_count=0,
                failed_fact_count=0,
                failure_stage="interpretation",
                failure_reason=str(exc),
            )

        extraction_run = self.extraction_repository.get_latest_run_for_document(result_document_id)
        if extraction_run is None:
            self.document_lifecycle_repository.force_state(document, DocumentState.INTERPRETATION_FAILED)
            self.session.commit()
            return DocumentSemanticProcessingResult(
                extraction_status="interpretation_failed",
                document_state=DocumentState.INTERPRETATION_FAILED.value,
                canonical_metric_count=0,
                failed_fact_count=0,
                failure_stage="interpretation",
                failure_reason="missing_extraction_run_after_pipeline",
            )

        document.contract_version_used = extraction_run.contract_version
        self.session.add(document)
        self.session.flush()

        normalized_company = self.canonization_service.company_normalizer.normalize(
            contract.document.company_reported_name
        )
        if normalized_company is not None:
            self.document_version_repository.ensure_document_version(
                result_document_id=result_document_id,
                company_id=normalized_company.id,
                reference_year=contract.document.reference_period.year,
                reference_quarter=contract.document.reference_period.quarter,
            )

        try:
            canonization_result = self.canonization_service.canonize(
                extraction_run=extraction_run,
                contract=contract,
                result_document_id=result_document_id,
                current_document_state=document.current_state,
            )
        except Exception as exc:
            self.document_lifecycle_repository.force_state(document, DocumentState.CANONICALIZATION_FAILED)
            self.session.commit()
            return DocumentSemanticProcessingResult(
                extraction_status="canonicalization_failed",
                document_state=DocumentState.CANONICALIZATION_FAILED.value,
                canonical_metric_count=0,
                failed_fact_count=0,
                extraction_run_id=extraction_run.id,
                failure_stage="canonicalization",
                failure_reason=str(exc),
            )

        if normalized_company is not None and canonization_result.document_state == DocumentState.CANONICAL.value:
            self.canonical_source_service.reevaluate_scope(
                company_id=normalized_company.id,
                reference_year=contract.document.reference_period.year,
                reference_quarter=contract.document.reference_period.quarter,
            )
        return DocumentSemanticProcessingResult(
            extraction_status=extraction_run.status,
            document_state=canonization_result.document_state,
            canonical_metric_count=canonization_result.canonical_metric_count,
            failed_fact_count=canonization_result.failed_fact_count,
            extraction_run_id=extraction_run.id,
            failure_stage="canonicalization"
            if canonization_result.document_state == DocumentState.CANONICALIZATION_FAILED.value
            else None,
            failure_reason=canonization_result.failure_reason,
        )
