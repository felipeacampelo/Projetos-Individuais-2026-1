from __future__ import annotations

from app.config import Settings
from app.extraction.llm.factory import build_llm_extraction_client
from app.extraction.llm.heuristic import HeuristicExtractionClient
from app.extraction.llm.openai_client import OpenAIExtractionClient


def test_openai_client_parses_json_content() -> None:
    client = OpenAIExtractionClient(
        api_key="test-key",
        model="gpt-4o-mini",
        contract_version="1.0.0",
    )

    payload = client._parse_json_content(
        '{"contract_version":"1.0.0","extraction_id":"x","document":{"source_url":"https://example.com/doc.pdf","document_type":"previa_operacional","company_reported_name":"MRV","reference_period":{"year":2025,"quarter":3}},"facts":[],"warnings":[]}'
    )

    assert payload["contract_version"] == "1.0.0"
    assert payload["document"]["document_type"] == "previa_operacional"


def test_openai_client_builds_from_settings() -> None:
    settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        llm_api_key="secret",
        semantic_contract_version="1.0.0",
    )

    client = OpenAIExtractionClient.from_settings(settings)

    assert client.provider_name == "openai"
    assert client.model_name == "gpt-4o-mini"
    assert client.contract_version == "1.0.0"


def test_factory_falls_back_to_heuristic_without_api_key() -> None:
    from app.extraction.llm import factory as factory_module

    original = factory_module.get_settings
    factory_module.get_settings = lambda: Settings(llm_provider="openai", llm_api_key="")
    try:
        client = build_llm_extraction_client()
    finally:
        factory_module.get_settings = original

    assert isinstance(client, HeuristicExtractionClient)
