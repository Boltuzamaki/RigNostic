"""Minimal model-provider factory supporting Gemini and OpenAI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from google import genai
from google.genai import types
from openai import OpenAI

from rignostic.config import BaselineConfig


@dataclass(frozen=True)
class ModelResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class ModelClient(Protocol):
    def generate(self, prompt: str) -> ModelResponse: ...


def infer_provider(model: str) -> str:
    if model.startswith("gemini-"):
        return "gemini"
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    raise ValueError(f"Cannot infer provider from model {model!r}; set RIGNOSTIC_PROVIDER")


class GeminiClient:
    def __init__(self, config: BaselineConfig) -> None:
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError("Gemini requires GEMINI_API_KEY or GOOGLE_API_KEY")
        self.config = config
        self.client = genai.Client(api_key=key)

    def generate(self, prompt: str) -> ModelResponse:
        response = self.client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
            ),
        )
        usage = response.usage_metadata
        return ModelResponse(
            text=response.text or "",
            input_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
        )


class OpenAIClient:
    def __init__(self, config: BaselineConfig) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OpenAI requires OPENAI_API_KEY")
        self.config = config
        self.client = OpenAI()

    def generate(self, prompt: str) -> ModelResponse:
        response = self.client.responses.create(
            model=self.config.model,
            input=prompt,
            max_output_tokens=self.config.max_output_tokens,
        )
        return ModelResponse(
            text=response.output_text,
            input_tokens=getattr(response.usage, "input_tokens", None),
            output_tokens=getattr(response.usage, "output_tokens", None),
        )


def create_model_client(config: BaselineConfig) -> ModelClient:
    provider = config.provider if config.provider != "auto" else infer_provider(config.model)
    if provider == "gemini":
        return GeminiClient(config)
    if provider == "openai":
        return OpenAIClient(config)
    raise ValueError(f"Unsupported model provider: {provider}")
