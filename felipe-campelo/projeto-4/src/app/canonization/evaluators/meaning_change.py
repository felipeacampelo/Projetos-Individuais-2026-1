from __future__ import annotations

from app.extraction.contracts.semantic_contract import CandidateFactContract


class MeaningChangeGuard:
    def is_blocked(self, fact: CandidateFactContract, warnings: list[dict] | None = None) -> bool:
        if warnings is None:
            return False
        return any(warning.get("code") == "possible_meaning_change" for warning in warnings)
