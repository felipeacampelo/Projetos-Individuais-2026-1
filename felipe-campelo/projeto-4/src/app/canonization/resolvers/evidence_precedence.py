from __future__ import annotations

from app.extraction.contracts.semantic_contract import CandidateFactContract


class EvidencePrecedencePolicy:
    def rank(self, fact: CandidateFactContract) -> tuple[int, int]:
        section = (fact.evidence.section or "").lower()
        if "tabela" in section or "table" in section:
            return (0, fact.evidence.page or 9999)
        if "operacion" in section or "destaque" in section or "summary" in section:
            return (1, fact.evidence.page or 9999)
        return (2, fact.evidence.page or 9999)

    def choose_best(self, facts: list[CandidateFactContract]) -> list[CandidateFactContract]:
        return sorted(facts, key=self.rank)
