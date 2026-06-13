from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.canonization.service import CanonizationService
from app.domain.document_lifecycle import DocumentState
from app.extraction.llm.heuristic import HeuristicExtractionClient
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


class DocumentSemanticProcessingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.extraction_pipeline = SemanticExtractionPipeline(session=session, llm_client=HeuristicExtractionClient())
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
        except Exception:
            self.document_lifecycle_repository.force_state(document, DocumentState.INTERPRETATION_FAILED)
            self.session.commit()
            return DocumentSemanticProcessingResult(
                extraction_status="interpretation_failed",
                document_state=DocumentState.INTERPRETATION_FAILED.value,
                canonical_metric_count=0,
                failed_fact_count=0,
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
            )

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
        except Exception:
            self.document_lifecycle_repository.force_state(document, DocumentState.CANONICALIZATION_FAILED)
            self.session.commit()
            return DocumentSemanticProcessingResult(
                extraction_status="canonicalization_failed",
                document_state=DocumentState.CANONICALIZATION_FAILED.value,
                canonical_metric_count=0,
                failed_fact_count=0,
            )
        return DocumentSemanticProcessingResult(
            extraction_status=extraction_run.status,
            document_state=canonization_result.document_state,
            canonical_metric_count=canonization_result.canonical_metric_count,
            failed_fact_count=canonization_result.failed_fact_count,
        )
