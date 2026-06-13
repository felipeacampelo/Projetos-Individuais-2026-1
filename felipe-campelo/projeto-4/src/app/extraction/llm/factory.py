from __future__ import annotations

from app.config import get_settings
from app.extraction.llm.base import LLMExtractionClient
from app.extraction.llm.heuristic import HeuristicExtractionClient
from app.extraction.llm.openai_client import OpenAIExtractionClient


def build_llm_extraction_client() -> LLMExtractionClient:
    settings = get_settings()
    provider = settings.llm_provider.strip().lower()

    if provider == "openai" and settings.llm_api_key:
        return OpenAIExtractionClient.from_settings(settings)

    return HeuristicExtractionClient()
