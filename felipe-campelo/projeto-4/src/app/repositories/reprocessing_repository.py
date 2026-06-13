from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ReprocessingRequest, ResultDocument


class ReprocessingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_request(
        self,
        *,
        result_document_id: int,
        trigger_type: str,
        trigger_version: str,
        status: str = "pending",
    ) -> ReprocessingRequest:
        existing = self.session.scalar(
            select(ReprocessingRequest).where(
                ReprocessingRequest.result_document_id == result_document_id,
                ReprocessingRequest.trigger_type == trigger_type,
                ReprocessingRequest.trigger_version == trigger_version,
            )
        )
        if existing is not None:
            return existing

        request = ReprocessingRequest(
            result_document_id=result_document_id,
            trigger_type=trigger_type,
            trigger_version=trigger_version,
            status=status,
        )
        self.session.add(request)
        self.session.flush()
        return request

    def list_pending(self) -> list[ReprocessingRequest]:
        stmt = select(ReprocessingRequest).where(ReprocessingRequest.status == "pending")
        return list(self.session.scalars(stmt))

    def mark_completed(self, request: ReprocessingRequest) -> ReprocessingRequest:
        request.status = "completed"
        self.session.add(request)
        self.session.flush()
        return request

    def list_documents_eligible_for_material_reprocessing(
        self,
        *,
        semantic_contract_version: str,
        normalization_knowledge_version: str,
    ) -> list[ResultDocument]:
        stmt = select(ResultDocument).where(
            ResultDocument.current_state.in_(
                ["recovery_failed", "interpretation_failed", "canonicalization_failed", "canonical"]
            )
        )
        documents = list(self.session.scalars(stmt))
        return [
            document
            for document in documents
            if self.requires_material_reprocessing(
                document=document,
                semantic_contract_version=semantic_contract_version,
                normalization_knowledge_version=normalization_knowledge_version,
            )
        ]

    @staticmethod
    def requires_material_reprocessing(
        *,
        document: ResultDocument,
        semantic_contract_version: str,
        normalization_knowledge_version: str,
    ) -> bool:
        if document.current_state in {"recovery_failed", "interpretation_failed"}:
            return True
        if document.contract_version_used != semantic_contract_version:
            return True
        if document.normalization_version_used != normalization_knowledge_version:
            return True
        return False
