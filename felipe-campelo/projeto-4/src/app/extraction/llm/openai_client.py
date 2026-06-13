from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.config import Settings
from app.extraction.contracts.semantic_contract import SemanticExtractionContract
from app.extraction.llm.base import LLMExtractionClient
from app.extraction.pipelines.document_preparation import PreparedDocumentForExtraction


@dataclass(frozen=True)
class OpenAIExtractionClient(LLMExtractionClient):
    api_key: str
    model: str
    contract_version: str
    base_url: str = "https://api.openai.com/v1"

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenAIExtractionClient":
        return cls(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            contract_version=settings.semantic_contract_version,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self.model

    def extract(
        self,
        *,
        prepared_document: PreparedDocumentForExtraction,
        source_url: str,
        document_type: str,
    ) -> SemanticExtractionContract:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": self._build_system_prompt()},
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        prepared_document=prepared_document,
                        source_url=source_url,
                        document_type=document_type,
                    ),
                },
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        body = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed_payload = self._parse_json_content(content)
        contract = SemanticExtractionContract.model_validate(parsed_payload)
        if contract.contract_version != self.contract_version:
            contract = contract.model_copy(update={"contract_version": self.contract_version})
        return contract

    def _build_system_prompt(self) -> str:
        return (
            "You extract a strict semantic JSON contract from Brazilian investor relations PDFs. "
            "Return valid JSON only. "
            "Never include markdown fences, prose, or comments. "
            "If a metric is not clearly supported by the text, omit it. "
            "Keep evidence snippets literal and short."
        )

    def _build_user_prompt(
        self,
        *,
        prepared_document: PreparedDocumentForExtraction,
        source_url: str,
        document_type: str,
    ) -> str:
        candidate_pages = {chunk.page_number for chunk in prepared_document.chunking_plan.candidate_chunks}
        pages_payload = []
        for page in prepared_document.parsed_document.pages:
            if candidate_pages and page.page_number not in candidate_pages:
                continue
            pages_payload.append(
                {
                    "page_number": page.page_number,
                    "text": page.text[:6000],
                }
            )

        schema_hint = {
            "contract_version": self.contract_version,
            "extraction_id": "slug-like string",
            "document": {
                "source_url": source_url,
                "document_type": document_type,
                "company_reported_name": "string or null",
                "reference_period": {"year": 2025, "quarter": 3},
            },
            "facts": [
                {
                    "reported_metric_name": "string",
                    "candidate_metric_category": "operacional|mercado_habitacional|desconhecida",
                    "value_status": "reported|missing",
                    "reported_value": 0.0,
                    "reported_unit": "string or null",
                    "canonical_numeric_value": 0.0,
                    "canonical_unit_hint": "string or null",
                    "comparative_values": [],
                    "cuts": [],
                    "evidence": {"page": 1, "section": None, "snippet": "literal snippet"},
                }
            ],
            "warnings": [],
        }

        return (
            "Extract the semantic contract for the investor relations document.\n"
            f"Required contract_version: {self.contract_version}\n"
            f"Source URL: {source_url}\n"
            f"Document type hint: {document_type}\n"
            "Use only facts explicitly supported by the pages below.\n"
            "Prefer quarterly operational and housing metrics like VSO, vendas liquidas, lancamentos, estoque, unidades vendidas.\n"
            "Return JSON matching this shape exactly:\n"
            f"{json.dumps(schema_hint, ensure_ascii=True)}\n"
            "Pages:\n"
            f"{json.dumps(pages_payload, ensure_ascii=True)}"
        )

    @staticmethod
    def _parse_json_content(content: str) -> dict:
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.strip("`")
            normalized = normalized.replace("json", "", 1).strip()
        return json.loads(normalized)
