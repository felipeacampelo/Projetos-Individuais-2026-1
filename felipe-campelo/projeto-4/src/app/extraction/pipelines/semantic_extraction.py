from __future__ import annotations

from sqlalchemy.orm import Session

from app.extraction.contracts.semantic_contract import SemanticExtractionContract
from app.extraction.llm.base import LLMExtractionClient
from app.extraction.pipelines.document_preparation import DocumentPreparationPipeline
from app.repositories.extraction_repository import ExtractionRepository


class SemanticExtractionPipeline:
    def __init__(
        self,
        session: Session,
        llm_client: LLMExtractionClient,
        document_preparation_pipeline: DocumentPreparationPipeline | None = None,
    ) -> None:
        self.session = session
        self.llm_client = llm_client
        self.document_preparation_pipeline = document_preparation_pipeline or DocumentPreparationPipeline()
        self.repository = ExtractionRepository(session)

    def run(
        self,
        *,
        result_document_id: int,
        content: bytes,
        source_url: str,
        document_type: str,
    ) -> SemanticExtractionContract:
        prepared_document = self.document_preparation_pipeline.prepare(content)
        contract = self.llm_client.extract(
            prepared_document=prepared_document,
            source_url=source_url,
            document_type=document_type,
        )

        extraction_run = self.repository.create_extraction_run(
            result_document_id=result_document_id,
            contract_version=contract.contract_version,
            llm_provider=self.llm_client.provider_name,
            llm_model=self.llm_client.model_name,
            status="extracted",
            raw_contract_payload=contract.model_dump(mode="json"),
        )
        self.repository.persist_contract_facts(
            extraction_run_id=extraction_run.id,
            contract=contract,
        )
        self.repository.mark_run_finished(extraction_run, status="extracted")
        self.session.commit()
        return contract
