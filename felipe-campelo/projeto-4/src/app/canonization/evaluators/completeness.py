from __future__ import annotations

from app.extraction.contracts.semantic_contract import CandidateFactContract, DocumentContract


class SemanticCompletenessEvaluator:
    def is_document_complete(self, document: DocumentContract, facts: list[CandidateFactContract]) -> bool:
        if not document.company_reported_name:
            return False
        if not facts:
            return False
        return any(fact.evidence.snippet.strip() for fact in facts)
