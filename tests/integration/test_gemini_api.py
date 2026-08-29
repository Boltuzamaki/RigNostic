"""Opt-in live Gemini API smoke test.

Enable with RIGNOSTIC_RUN_LIVE_MODEL_TESTS=1. This test incurs a small API call.
"""

import os

import pytest

from rignostic.config import load_config
from rignostic.models import create_model_client

pytestmark = pytest.mark.live_model


def test_configured_gemini_model_responds() -> None:
    if os.getenv("RIGNOSTIC_RUN_LIVE_MODEL_TESTS") != "1":
        pytest.skip("set RIGNOSTIC_RUN_LIVE_MODEL_TESTS=1 to make a live API call")

    config = load_config().baseline
    assert config.model.startswith("gemini-")
    assert os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    response = create_model_client(config).generate(
        "Reply with exactly RIGNOSTIC_MODEL_OK and no other text."
    )

    assert response.text.strip() == "RIGNOSTIC_MODEL_OK"
    assert response.input_tokens is None or response.input_tokens > 0
    assert response.output_tokens is None or response.output_tokens > 0

