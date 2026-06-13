from __future__ import annotations

from dataclasses import dataclass

from app.extraction.contracts.semantic_contract import CandidateCutContract


@dataclass(frozen=True)
class NormalizedCut:
    dimension: str
    value: str


class CutNormalizationError(ValueError):
    """Raised when a material cut cannot be normalized."""


class CutNormalizer:
    DIMENSION_ALIASES = {
        "escopo": "escopo",
        "scope": "escopo",
        "região": "regiao",
        "regiao": "regiao",
        "region": "regiao",
        "segmento": "segmento",
        "segment": "segmento",
        "produto": "produto",
        "product": "produto",
    }

    VALUE_ALIASES = {
        "consolidado": "consolidado",
        "consolidated": "consolidado",
    }

    def normalize_many(self, cuts: list[CandidateCutContract]) -> list[NormalizedCut]:
        return [self.normalize(cut) for cut in cuts]

    def normalize(self, cut: CandidateCutContract) -> NormalizedCut:
        dimension = self.DIMENSION_ALIASES.get(cut.dimension_label.strip().lower())
        value = self.VALUE_ALIASES.get(cut.value_label.strip().lower(), cut.value_label.strip().lower())

        if dimension is None and cut.is_material:
            raise CutNormalizationError(f"Unsupported material cut dimension: {cut.dimension_label}")
        if dimension is None:
            dimension = "desconhecida"

        if not value and cut.is_material:
            raise CutNormalizationError("Missing material cut value")

        return NormalizedCut(dimension=dimension, value=value or "desconhecido")
