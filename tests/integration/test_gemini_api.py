"""Opt-in live default-model smoke test.

Enable with RIGNOSTIC_RUN_LIVE_MODEL_TESTS=1. This test incurs a small API call.
"""

import json
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
        'Return JSON only: {"status":"RIGNOSTIC_MODEL_OK"}'
    )

    assert json.loads(response.text)["status"] == "RIGNOSTIC_MODEL_OK"
    assert response.input_tokens is None or response.input_tokens > 0
    assert response.output_tokens is None or response.output_tokens > 0
