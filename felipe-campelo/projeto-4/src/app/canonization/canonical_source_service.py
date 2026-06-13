from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.canonization.evaluators.completeness import SemanticCompletenessEvaluator
from app.canonization.resolvers.document_precedence import DocumentPrecedencePolicy
from app.db.models import CanonicalMetric, ResultDocument
from app.domain.document_lifecycle import DocumentState
from app.repositories.canonical_metric_repository import CanonicalMetricRepository
from app.repositories.document_lifecycle_repository import DocumentLifecycleRepository
from app.repositories.extraction_repository import ExtractionRepository
from app.repositories.result_document_repository import ResultDocumentRepository


@dataclass(frozen=True)
class CanonicalSourceDecision:
    winning_document_id: int
    superseded_document_ids: list[int]
    deleted_metric_count: int = 0
    winning_completeness_score: int | None = None


class ReevaluateCanonicalSourceService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.canonical_metric_repository = CanonicalMetricRepository(session)
        self.document_repository = ResultDocumentRepository(session)
        self.document_lifecycle_repository = DocumentLifecycleRepository(session)
        self.document_precedence_policy = DocumentPrecedencePolicy()
        self.extraction_repository = ExtractionRepository(session)
        self.completeness_evaluator = SemanticCompletenessEvaluator()

    def reevaluate_scope(
        self,
        *,
        company_id: int,
        reference_year: int,
        reference_quarter: int,
    ) -> CanonicalSourceDecision | None:
        metrics = self.canonical_metric_repository.list_for_scope(
            company_id=company_id,
            reference_year=reference_year,
            reference_quarter=reference_quarter,
        )
        if not metrics:
            return None

        documents_by_id: dict[int, ResultDocument] = {}
        for metric in metrics:
            if metric.result_document_id in documents_by_id:
                continue
            document = self.document_repository.get_by_id(metric.result_document_id)
            if document is not None:
                documents_by_id[document.id] = document

        if len(documents_by_id) <= 1:
            only_document = next(iter(documents_by_id.values()))
            if only_document.current_state != DocumentState.CANONICAL.value:
                self.document_lifecycle_repository.force_state(only_document, DocumentState.CANONICAL)
                self.session.commit()
            return CanonicalSourceDecision(
                winning_document_id=only_document.id,
                superseded_document_ids=[],
                deleted_metric_count=0,
                winning_completeness_score=len(metrics) * 100,
            )

        winner = self._pick_winner(list(documents_by_id.values()))
        superseded_ids: list[int] = []
        deleted_metric_count = 0
        for document in documents_by_id.values():
            if document.id == winner.id:
                self.document_lifecycle_repository.force_state(document, DocumentState.CANONICAL)
                continue
            deleted_metric_count += len(self.canonical_metric_repository.list_for_document(document.id))
            self.canonical_metric_repository.delete_for_document(document.id)
            self.document_lifecycle_repository.force_state(document, DocumentState.SUPERSEDED)
            superseded_ids.append(document.id)

        self.session.commit()
        return CanonicalSourceDecision(
            winning_document_id=winner.id,
            superseded_document_ids=superseded_ids,
            deleted_metric_count=deleted_metric_count,
            winning_completeness_score=self._score_document(winner, metrics).total,
        )

    def _pick_winner(self, documents: list[ResultDocument]) -> ResultDocument:
        winner = documents[0]
        for candidate in documents[1:]:
            winner_priority = self.document_precedence_policy.priority_for(winner.document_type)
            candidate_priority = self.document_precedence_policy.priority_for(candidate.document_type)

            if candidate_priority < winner_priority:
                winner = candidate
                continue
            if candidate_priority > winner_priority:
                continue

            winner_score = self._score_document(winner)
            candidate_score = self._score_document(candidate)
            if candidate_score.total > winner_score.total:
                winner = candidate
                continue
            if candidate_score.total == winner_score.total and candidate.id > winner.id:
                winner = candidate
        return winner

    def _score_document(
        self,
        document: ResultDocument,
        metrics: list[CanonicalMetric] | None = None,
    ):
        metric_count = len(
            metrics_for_document(metrics, document.id)
            if metrics is not None
            else self.canonical_metric_repository.list_for_document(document.id)
        )
        extraction_run = self.extraction_repository.get_latest_run_detail_for_document(document.id)
        return self.completeness_evaluator.score_extraction_run(
            extraction_run=extraction_run,
            canonical_metric_count=metric_count,
        )


def metrics_for_document(metrics: list[CanonicalMetric], document_id: int) -> list[CanonicalMetric]:
    return [metric for metric in metrics if metric.result_document_id == document_id]
