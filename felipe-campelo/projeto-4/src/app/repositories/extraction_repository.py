from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.canonization.normalizers.metric import MetricNormalizer
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

    def get_latest_run_for_document(self, result_document_id: int) -> ExtractionRun | None:
        stmt = (
            select(ExtractionRun)
            .where(ExtractionRun.result_document_id == result_document_id)
            .order_by(ExtractionRun.id.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_latest_run_detail_for_document(self, result_document_id: int) -> ExtractionRun | None:
        stmt = (
            select(ExtractionRun)
            .where(ExtractionRun.result_document_id == result_document_id)
            .order_by(ExtractionRun.id.desc())
            .limit(1)
            .options(
                joinedload(ExtractionRun.candidate_facts).joinedload(CandidateFact.cuts),
                joinedload(ExtractionRun.candidate_facts).joinedload(CandidateFact.evidence_items),
            )
        )
        return self.session.scalar(stmt)

    def list_runs(self, *, result_document_id: int | None = None) -> list[ExtractionRun]:
        stmt = (
            select(ExtractionRun)
            .options(joinedload(ExtractionRun.result_document))
            .order_by(ExtractionRun.id.desc())
        )
        if result_document_id is not None:
            stmt = stmt.where(ExtractionRun.result_document_id == result_document_id)
        return list(self.session.scalars(stmt))

    def get_run_detail(self, extraction_run_id: int) -> ExtractionRun | None:
        stmt = (
            select(ExtractionRun)
            .where(ExtractionRun.id == extraction_run_id)
            .options(
                joinedload(ExtractionRun.result_document),
                joinedload(ExtractionRun.candidate_facts).joinedload(CandidateFact.cuts),
                joinedload(ExtractionRun.candidate_facts).joinedload(CandidateFact.evidence_items),
            )
        )
        return self.session.scalar(stmt)

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

    def get_document_metric_evidence(
        self,
        *,
        result_document_id: int,
        metric_slug: str,
    ) -> ExtractionEvidence | None:
        stmt = (
            select(CandidateFact)
            .join(ExtractionRun, ExtractionRun.id == CandidateFact.extraction_run_id)
            .where(ExtractionRun.result_document_id == result_document_id)
            .order_by(CandidateFact.id.asc())
        )
        metric_normalizer = MetricNormalizer(self.session)
        for candidate_fact in self.session.scalars(stmt):
            normalized = metric_normalizer.normalize(candidate_fact.reported_metric_name)
            if normalized is None:
                continue
            if normalized.metric_catalog_item.slug != metric_slug:
                continue
            evidence_stmt = (
                select(ExtractionEvidence)
                .where(ExtractionEvidence.candidate_fact_id == candidate_fact.id)
                .order_by(ExtractionEvidence.id.asc())
                .limit(1)
            )
            return self.session.scalar(evidence_stmt)
        return None
