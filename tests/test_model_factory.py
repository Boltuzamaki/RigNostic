import pytest

from rignostic.config import BaselineConfig
from rignostic.models.factory import GeminiClient, OpenAIClient, create_model_client, infer_provider


def test_provider_inference() -> None:
    assert infer_provider("gemini-3.5-flash-lite") == "gemini"
    assert infer_provider("gpt-5-mini") == "openai"


def test_unknown_model_requires_explicit_provider() -> None:
    with pytest.raises(ValueError):
        infer_provider("custom-model")


def test_factory_selects_gemini(monkeypatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    client = create_model_client(BaselineConfig(model="gemini-3.5-flash-lite"))
    assert isinstance(client, GeminiClient)


def test_factory_selects_openai(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    client = create_model_client(BaselineConfig(provider="openai", model="custom-model"))
    assert isinstance(client, OpenAIClient)
