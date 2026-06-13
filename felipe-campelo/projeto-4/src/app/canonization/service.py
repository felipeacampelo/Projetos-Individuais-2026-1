from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.canonization.evaluators.completeness import SemanticCompletenessEvaluator
from app.canonization.evaluators.meaning_change import MeaningChangeGuard
from app.canonization.normalizers.company import CompanyNormalizer
from app.canonization.normalizers.cut import CutNormalizationError, CutNormalizer
from app.canonization.normalizers.metric import MetricNormalizer
from app.canonization.normalizers.unit import UnitNormalizationError, UnitNormalizer
from app.db.models import ExtractionRun
from app.domain.document_lifecycle import DocumentState
from app.extraction.contracts.semantic_contract import SemanticExtractionContract
from app.repositories.canonical_metric_repository import CanonicalMetricRepository
from app.repositories.document_lifecycle_repository import DocumentLifecycleRepository
from app.repositories.result_document_repository import ResultDocumentRepository


@dataclass(frozen=True)
class CanonizationResult:
    canonical_metric_count: int
    failed_fact_count: int
    document_state: str
    failure_reason: str | None = None


class CanonizationService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.company_normalizer = CompanyNormalizer(session)
        self.metric_normalizer = MetricNormalizer(session)
        self.unit_normalizer = UnitNormalizer()
        self.cut_normalizer = CutNormalizer()
        self.completeness_evaluator = SemanticCompletenessEvaluator()
        self.meaning_change_guard = MeaningChangeGuard()
        self.canonical_metric_repository = CanonicalMetricRepository(session)
        self.document_lifecycle_repository = DocumentLifecycleRepository(session)
        self.result_document_repository = ResultDocumentRepository(session)

    def canonize(
        self,
        *,
        extraction_run: ExtractionRun,
        contract: SemanticExtractionContract,
        result_document_id: int,
        current_document_state: str,
    ) -> CanonizationResult:
        document = self.result_document_repository.get_by_id(result_document_id)
        if document is not None:
            document.normalization_version_used = self.settings.normalization_knowledge_version
            self.session.add(document)
            self.session.flush()

        if not self.completeness_evaluator.is_document_complete(contract.document, contract.facts):
            self._sync_document_state(result_document_id, current_document_state, DocumentState.CANONICALIZATION_FAILED)
            return CanonizationResult(
                canonical_metric_count=0,
                failed_fact_count=len(contract.facts),
                document_state=DocumentState.CANONICALIZATION_FAILED.value,
                failure_reason="document_not_semantically_complete",
            )

        normalized_company = self.company_normalizer.normalize(contract.document.company_reported_name)
        if normalized_company is None:
            self._sync_document_state(result_document_id, current_document_state, DocumentState.CANONICALIZATION_FAILED)
            return CanonizationResult(
                canonical_metric_count=0,
                failed_fact_count=len(contract.facts),
                document_state=DocumentState.CANONICALIZATION_FAILED.value,
                failure_reason="company_not_normalized",
            )

        created_count = 0
        failed_count = 0
        warning_dicts = [warning.model_dump() for warning in contract.warnings]

        for fact in contract.facts:
            if self.meaning_change_guard.is_blocked(fact, warning_dicts):
                failed_count += 1
                continue

            normalized_metric = self.metric_normalizer.normalize(fact.reported_metric_name)
            if normalized_metric is None:
                failed_count += 1
                continue

            try:
                canonical_unit = self.unit_normalizer.normalize(
                    fact.reported_unit,
                    fact.canonical_unit_hint,
                )
                normalized_value = self.unit_normalizer.normalize_value(
                    fact.reported_value,
                    fact.reported_unit,
                    canonical_unit,
                )
                normalized_cuts = self.cut_normalizer.normalize_many(fact.cuts)
            except (UnitNormalizationError, CutNormalizationError):
                failed_count += 1
                continue

            canonical_metric = self.canonical_metric_repository.create_metric(
                company_id=normalized_company.id,
                result_document_id=result_document_id,
                metric_catalog_item_id=normalized_metric.metric_catalog_item.id,
                reference_year=contract.document.reference_period.year,
                reference_quarter=contract.document.reference_period.quarter,
                value=normalized_value if fact.value_status == "reported" else None,
                value_status=fact.value_status,
                canonical_unit=canonical_unit,
                reported_value=fact.reported_value,
                reported_unit=fact.reported_unit,
            )
            for cut in normalized_cuts:
                self.canonical_metric_repository.add_cut(
                    canonical_metric_id=canonical_metric.id,
                    dimension=cut.dimension,
                    value=cut.value,
                )
            created_count += 1

        new_state = (
            DocumentState.CANONICAL
            if created_count > 0
            else DocumentState.CANONICALIZATION_FAILED
        )
        extraction_run.status = "canonicalized" if created_count > 0 else "canonicalization_failed"
        self.session.add(extraction_run)
        self._sync_document_state(result_document_id, current_document_state, new_state)
        self.session.commit()

        return CanonizationResult(
            canonical_metric_count=created_count,
            failed_fact_count=failed_count,
            document_state=new_state.value,
            failure_reason=None if created_count > 0 else "no_fact_could_be_canonicalized",
        )

    def _sync_document_state(
        self,
        result_document_id: int,
        current_document_state: str,
        target_state: DocumentState,
    ) -> None:
        document = self.result_document_repository.get_by_id(result_document_id)
        if document is None:
            return

        current_state = DocumentState(current_document_state)
        if current_state == target_state:
            return

        if current_state == DocumentState.OBSERVED:
            self.document_lifecycle_repository.force_state(document, DocumentState.EXTRACTED)
            current_state = DocumentState.EXTRACTED

        if current_state == DocumentState.EXTRACTED:
            self.document_lifecycle_repository.transition_state(document, target_state)
            return

        self.document_lifecycle_repository.force_state(document, target_state)
