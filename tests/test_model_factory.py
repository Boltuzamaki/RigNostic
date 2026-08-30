from types import SimpleNamespace

import pytest

from rignostic.config import BaselineConfig
from rignostic.models.factory import (
    LiteLLMClient,
    create_model_client,
    infer_provider,
    litellm_model_name,
)


def test_provider_inference() -> None:
    assert infer_provider("gemini-3.5-flash-lite") == "gemini"
    assert infer_provider("gpt-5-mini") == "openai"
    assert infer_provider("anthropic/claude-sonnet-4-5") == "anthropic"


def test_unknown_model_requires_provider() -> None:
    with pytest.raises(ValueError):
        infer_provider("custom-model")


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        (BaselineConfig(model="gemini-3.5-flash-lite"), "gemini/gemini-3.5-flash-lite"),
        (BaselineConfig(provider="openai", model="custom-model"), "openai/custom-model"),
        (BaselineConfig(model="ollama/qwen3:8b"), "ollama/qwen3:8b"),
    ],
)
def test_litellm_model_name(config: BaselineConfig, expected: str) -> None:
    assert litellm_model_name(config) == expected


def test_factory_uses_litellm() -> None:
    client = create_model_client(BaselineConfig(model="gemini-3.5-flash-lite"))
    assert isinstance(client, LiteLLMClient)


def test_generate_maps_text_and_usage(monkeypatch) -> None:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"detected_defects":[]}'))],
        usage=SimpleNamespace(prompt_tokens=12, completion_tokens=7),
    )
    monkeypatch.setattr("rignostic.models.factory.litellm.completion", lambda **_: response)
    result = LiteLLMClient(BaselineConfig()).generate("inspect")
    assert result.text == '{"detected_defects":[]}'
    assert result.input_tokens == 12
    assert result.output_tokens == 7
