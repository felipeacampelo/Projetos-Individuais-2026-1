from __future__ import annotations

import re
from dataclasses import dataclass

from app.extraction.contracts.semantic_contract import (
    CandidateFactContract,
    CandidateMetricCategory,
    ComparativeValueContract,
    DocumentContract,
    EvidenceContract,
    ReferencePeriodContract,
    SemanticExtractionContract,
)
from app.extraction.llm.base import LLMExtractionClient
from app.extraction.pipelines.document_preparation import PreparedDocumentForExtraction


@dataclass(frozen=True)
class MetricRule:
    slug: str
    aliases: tuple[str, ...]
    category: CandidateMetricCategory
    expected_unit: str


METRIC_RULES: tuple[MetricRule, ...] = (
    MetricRule("vendas-liquidas", ("vendas liquidas", "vendas líquidas"), "operacional", "brl"),
    MetricRule("vso", ("vso", "velocidade de vendas"), "operacional", "percentage"),
    MetricRule("lancamentos-valor", ("lancamentos", "lançamentos"), "operacional", "brl"),
    MetricRule("lancamentos-unidades", ("unidades lancadas", "unidades lançadas"), "operacional", "units"),
    MetricRule("estoque-valor", ("estoque",), "operacional", "brl"),
    MetricRule("estoque-unidades", ("unidades em estoque", "estoque em unidades"), "operacional", "units"),
    MetricRule("unidades-vendidas", ("unidades vendidas", "qtd vendida"), "operacional", "units"),
)


class HeuristicExtractionClient(LLMExtractionClient):
    @property
    def provider_name(self) -> str:
        return "heuristic"

    @property
    def model_name(self) -> str:
        return "semantic-contract-heuristic-v1"

    def extract(
        self,
        *,
        prepared_document: PreparedDocumentForExtraction,
        source_url: str,
        document_type: str,
    ) -> SemanticExtractionContract:
        pages = prepared_document.parsed_document.pages
        candidate_page_numbers = {chunk.page_number for chunk in prepared_document.chunking_plan.candidate_chunks}
        relevant_pages = [page for page in pages if not candidate_page_numbers or page.page_number in candidate_page_numbers]

        facts: list[CandidateFactContract] = []
        seen_metric_slugs: set[str] = set()

        for page in relevant_pages:
            for line in self._iter_lines(page.text):
                normalized_line = self._normalize(line)
                for rule in METRIC_RULES:
                    if rule.slug in seen_metric_slugs:
                        continue
                    if not any(alias in normalized_line for alias in rule.aliases):
                        continue
                    fact = self._build_fact(rule=rule, line=line, page_number=page.page_number)
                    if fact is None:
                        continue
                    facts.append(fact)
                    seen_metric_slugs.add(rule.slug)

        return SemanticExtractionContract(
            contract_version="1.0.0",
            extraction_id=self._slugify_url(source_url),
            document=DocumentContract(
                source_url=source_url,
                document_type=document_type or "documento_resultado",
                company_reported_name=self._infer_company_name(pages),
                reference_period=self._infer_reference_period(pages),
            ),
            facts=facts,
            warnings=[],
        )

    def _build_fact(self, *, rule: MetricRule, line: str, page_number: int) -> CandidateFactContract | None:
        reported_value, reported_unit, comparative_values = self._extract_value_bundle(
            line=line,
            expected_unit=rule.expected_unit,
        )
        if reported_value is None or reported_unit is None:
            return None

        return CandidateFactContract(
            reported_metric_name=rule.slug,
            candidate_metric_category=rule.category,
            value_status="reported",
            reported_value=reported_value,
            reported_unit=reported_unit,
            canonical_numeric_value=reported_value,
            canonical_unit_hint=rule.expected_unit,
            comparative_values=comparative_values,
            cuts=[],
            evidence=EvidenceContract(page=page_number, section=None, snippet=line[:800]),
        )

    def _extract_value_bundle(
        self,
        *,
        line: str,
        expected_unit: str,
    ) -> tuple[float | None, str | None, list[ComparativeValueContract]]:
        comparative_values: list[ComparativeValueContract] = []
        if expected_unit == "brl":
            matches = re.findall(r"R\$\s*([\d\.\,]+)\s*(milh(?:ões|oes)|mil)?", line, flags=re.IGNORECASE)
            if not matches:
                return None, None, comparative_values
            raw_value, scale = matches[-1]
            if scale.lower().startswith("milh"):
                unit = "R$ milhões"
            elif scale:
                unit = "R$ mil"
            else:
                unit = "R$"
            return self._parse_number(raw_value), unit, comparative_values

        if expected_unit == "percentage":
            matches = re.findall(r"([\d\.\,]+)\s*%", line)
            if not matches:
                return None, None, comparative_values
            for extra_value in matches[1:]:
                comparative_values.append(
                    ComparativeValueContract(
                        kind="comparative_percentage",
                        value=self._parse_number(extra_value),
                        unit="%",
                    )
                )
            return self._parse_number(matches[0]), "%", comparative_values

        if expected_unit == "units":
            match = re.search(r"([\d\.\,]+)\s*(unidades|unidade|units)?", line, flags=re.IGNORECASE)
            if match is None:
                return None, None, comparative_values
            return self._parse_number(match.group(1)), "unidades", comparative_values

        return None, None, comparative_values

    def _infer_company_name(self, pages) -> str | None:
        text = "\n".join(page.text for page in pages[:2]).lower()
        if "mrv" in text:
            return "MRV"
        if "direcional" in text:
            return "Direcional"
        return None

    def _infer_reference_period(self, pages) -> ReferencePeriodContract:
        text = "\n".join(page.text for page in pages[:3])
        match = re.search(r"\b([1-4])T\s*(20\d{2}|\d{2})\b", text, flags=re.IGNORECASE)
        if match is None:
            match = re.search(
                r"\b([1-4])\s*trimestre\b.{0,20}\b(20\d{2})\b",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
        if match is None:
            return ReferencePeriodContract(year=2025, quarter=4)

        quarter = int(match.group(1))
        year = int(match.group(2))
        if year < 100:
            year += 2000
        return ReferencePeriodContract(year=year, quarter=quarter)

    @staticmethod
    def _iter_lines(text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.strip().lower()
        replacements = {
            "ç": "c",
            "ã": "a",
            "á": "a",
            "à": "a",
            "â": "a",
            "é": "e",
            "ê": "e",
            "í": "i",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ú": "u",
        }
        for original, replacement in replacements.items():
            normalized = normalized.replace(original, replacement)
        return normalized

    @staticmethod
    def _parse_number(raw_value: str) -> float:
        normalized = raw_value.strip()
        if "." in normalized and "," in normalized:
            normalized = normalized.replace(".", "").replace(",", ".")
        elif "," in normalized:
            normalized = normalized.replace(",", ".")
        return float(normalized)

    @staticmethod
    def _slugify_url(url: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")
