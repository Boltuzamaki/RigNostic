"""Model access through LiteLLM's provider-neutral completion API."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol

import litellm

from rignostic.config import BaselineConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class ModelClient(Protocol):
    def generate(self, prompt: str) -> ModelResponse: ...


def infer_provider(model: str) -> str:
    """Infer legacy unprefixed model names; prefixed LiteLLM names pass through."""
    if "/" in model:
        return model.split("/", 1)[0]
    if model.startswith("gemini-"):
        return "gemini"
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    raise ValueError(
        f"Cannot infer provider from model {model!r}; use provider/model or set RIGNOSTIC_PROVIDER"
    )


def litellm_model_name(config: BaselineConfig) -> str:
    """Convert old RigNostic settings into LiteLLM's provider/model format."""
    if "/" in config.model:
        return config.model
    provider = config.provider if config.provider != "auto" else infer_provider(config.model)
    return f"{provider}/{config.model}"


class LiteLLMClient:
    def __init__(self, config: BaselineConfig) -> None:
        self.config = config
        self.model = litellm_model_name(config)

    def generate(self, prompt: str) -> ModelResponse:
        logger.info("model_start model=%s", self.model)
        logger.debug("model_prompt characters=%s prompt=%s", len(prompt), prompt)
        started = time.monotonic()
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_output_tokens,
            response_format={"type": "json_object"},
        )
        choice = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        result = ModelResponse(
            text=choice,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )
        logger.info(
            "model_complete model=%s runtime_seconds=%.3f input_tokens=%s output_tokens=%s",
            self.model,
            time.monotonic() - started,
            result.input_tokens,
            result.output_tokens,
        )
        logger.debug("model_response %s", result.text)
        return result


def create_model_client(config: BaselineConfig) -> ModelClient:
    return LiteLLMClient(config)
