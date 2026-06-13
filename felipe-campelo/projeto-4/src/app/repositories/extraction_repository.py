from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import CandidateFact, CandidateFactCut, ExtractionEvidence, ExtractionRun
from app.extraction.contracts.semantic_contract import SemanticExtractionContract


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExtractionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_extraction_run(
        self,
        *,
        result_document_id: int,
        contract_version: str,
        llm_provider: str,
        llm_model: str,
        status: str,
        raw_contract_payload: dict,
    ) -> ExtractionRun:
        run = ExtractionRun(
            result_document_id=result_document_id,
            contract_version=contract_version,
            llm_provider=llm_provider,
            llm_model=llm_model,
            status=status,
            raw_contract_payload=raw_contract_payload,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def mark_run_finished(self, run: ExtractionRun, status: str) -> ExtractionRun:
        run.status = status
        run.finished_at = utc_now()
        self.session.add(run)
        self.session.flush()
        return run

    def persist_contract_facts(
        self,
        *,
        extraction_run_id: int,
        contract: SemanticExtractionContract,
    ) -> None:
        for fact in contract.facts:
            candidate_fact = CandidateFact(
                extraction_run_id=extraction_run_id,
                reported_metric_name=fact.reported_metric_name,
                candidate_metric_category=fact.candidate_metric_category,
                value_status=fact.value_status,
                reported_value=fact.reported_value,
                reported_unit=fact.reported_unit,
                canonical_numeric_value=fact.canonical_numeric_value,
                canonical_unit_hint=fact.canonical_unit_hint,
                warnings_json=[warning.model_dump() for warning in contract.warnings] or None,
            )
            self.session.add(candidate_fact)
            self.session.flush()

            for cut in fact.cuts:
                self.session.add(
                    CandidateFactCut(
                        candidate_fact_id=candidate_fact.id,
                        dimension_label=cut.dimension_label,
                        value_label=cut.value_label,
                        is_material=cut.is_material,
                    )
                )

            self.session.add(
                ExtractionEvidence(
                    candidate_fact_id=candidate_fact.id,
                    page_number=fact.evidence.page,
                    section_label=fact.evidence.section,
                    snippet=fact.evidence.snippet,
                )
            )
        self.session.flush()
