from __future__ import annotations


class UnitNormalizationError(ValueError):
    """Raised when the reported unit cannot be mapped to a canonical unit."""


class UnitNormalizer:
    def normalize(self, reported_unit: str | None, canonical_unit_hint: str | None = None) -> str:
        if canonical_unit_hint:
            return canonical_unit_hint
        if reported_unit is None:
            raise UnitNormalizationError("Missing reported unit")

        normalized = reported_unit.strip().lower()
        if normalized in {"r$ milhões", "r$ milhões ", "r$ milhoes", "r$ mil", "r$", "brl"}:
            return "brl"
        if normalized in {"%", "percent", "percentage"}:
            return "percentage"
        if normalized in {"p.p.", "pp", "percentage points"}:
            return "percentage_points"
        if normalized in {"unidades", "unidade", "units"}:
            return "units"
        raise UnitNormalizationError(f"Unsupported unit: {reported_unit}")

    def normalize_value(self, value: float | None, reported_unit: str | None, canonical_unit: str) -> float | None:
        if value is None:
            return None
        if canonical_unit != "brl" or reported_unit is None:
            return value

        normalized = reported_unit.strip().lower()
        if normalized in {"r$ milhões", "r$ milhoes"}:
            return value * 1_000_000
        if normalized in {"r$ mil"}:
            return value * 1_000
        return value
