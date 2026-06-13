from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import get_settings
from app.repositories.reprocessing_repository import ReprocessingRepository


class ReprocessingPlanner:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.repository = ReprocessingRepository(session)

    def enqueue_material_change_requests(
        self,
        *,
        trigger_type: str,
        trigger_version: str,
    ) -> int:
        eligible_documents = self.repository.list_documents_eligible_for_material_reprocessing(
            semantic_contract_version=(
                trigger_version if trigger_type == "semantic_contract_version" else self.settings.semantic_contract_version
            ),
            normalization_knowledge_version=(
                trigger_version
                if trigger_type == "normalization_knowledge_version"
                else self.settings.normalization_knowledge_version
            ),
        )
        created = 0
        for document in eligible_documents:
            request = self.repository.create_request(
                result_document_id=document.id,
                trigger_type=trigger_type,
                trigger_version=trigger_version,
            )
            if request.status == "pending":
                created += 1
        self.session.commit()
        return created
