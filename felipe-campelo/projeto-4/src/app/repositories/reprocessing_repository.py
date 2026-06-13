from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import ReprocessingRequest, ResultDocument


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


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

    def list_requests(self) -> list[ReprocessingRequest]:
        stmt = (
            select(ReprocessingRequest)
            .options(
                joinedload(ReprocessingRequest.result_document).joinedload(ResultDocument.company),
            )
            .order_by(ReprocessingRequest.id.desc())
        )
        return list(self.session.scalars(stmt))

    def get_request(self, request_id: int) -> ReprocessingRequest | None:
        stmt = (
            select(ReprocessingRequest)
            .where(ReprocessingRequest.id == request_id)
            .options(
                joinedload(ReprocessingRequest.result_document).joinedload(ResultDocument.company),
            )
        )
        return self.session.scalar(stmt)

    def mark_processing(self, request: ReprocessingRequest) -> ReprocessingRequest:
        request.status = "processing"
        request.started_at = utc_now()
        request.error_message = None
        self.session.add(request)
        self.session.flush()
        return request

    def mark_completed(self, request: ReprocessingRequest) -> ReprocessingRequest:
        request.status = "completed"
        request.finished_at = utc_now()
        request.error_message = None
        self.session.add(request)
        self.session.flush()
        return request

    def mark_failed(self, request: ReprocessingRequest, error_message: str) -> ReprocessingRequest:
        request.status = "failed"
        request.finished_at = utc_now()
        request.error_message = error_message
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
