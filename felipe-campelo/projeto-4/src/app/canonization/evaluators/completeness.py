from __future__ import annotations

from dataclasses import dataclass

from app.db.models import CandidateFact, ExtractionRun
from app.extraction.contracts.semantic_contract import CandidateFactContract, DocumentContract


@dataclass(frozen=True)
class SemanticCompletenessScore:
    canonical_metric_count: int
    reported_fact_count: int
    evidence_item_count: int
    material_cut_count: int
    warning_count: int

    @property
    def total(self) -> int:
        return (
            self.canonical_metric_count * 100
            + self.reported_fact_count * 10
            + self.evidence_item_count * 5
            + self.material_cut_count * 2
            - self.warning_count * 3
        )


class SemanticCompletenessEvaluator:
    def is_document_complete(self, document: DocumentContract, facts: list[CandidateFactContract]) -> bool:
        if not document.company_reported_name:
            return False
        if not facts:
            return False
        return any(fact.evidence.snippet.strip() for fact in facts)

    def score_extraction_run(
        self,
        *,
        extraction_run: ExtractionRun | None,
        canonical_metric_count: int,
    ) -> SemanticCompletenessScore:
        if extraction_run is None:
            return SemanticCompletenessScore(
                canonical_metric_count=canonical_metric_count,
                reported_fact_count=0,
                evidence_item_count=0,
                material_cut_count=0,
                warning_count=0,
            )

        facts = extraction_run.candidate_facts
        return SemanticCompletenessScore(
            canonical_metric_count=canonical_metric_count,
            reported_fact_count=sum(1 for fact in facts if fact.value_status == "reported"),
            evidence_item_count=sum(len(fact.evidence_items) for fact in facts),
            material_cut_count=sum(
                1 for fact in facts for cut in fact.cuts if cut.is_material
            ),
            warning_count=sum(len(fact.warnings_json or []) for fact in facts),
        )
