from __future__ import annotations

from abc import ABC, abstractmethod

from app.extraction.contracts.semantic_contract import SemanticExtractionContract
from app.extraction.pipelines.document_preparation import PreparedDocumentForExtraction


class LLMExtractionClient(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def extract(
        self,
        *,
        prepared_document: PreparedDocumentForExtraction,
        source_url: str,
        document_type: str,
    ) -> SemanticExtractionContract:
        raise NotImplementedError
