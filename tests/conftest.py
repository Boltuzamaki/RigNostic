"""Shared test fixtures and skip guards.

Several tests drive a real Blender binary through the runner. CI images do not
ship Blender, so those tests are skipped unless one is resolvable. Mirrors the
opt-in guard used for live model calls in tests/integration/test_gemini_api.py.
"""

from __future__ import annotations

import os
import shutil

import pytest


def blender_available() -> bool:
    """True when a usable Blender executable can be resolved."""
    configured = os.environ.get("BLENDER_EXECUTABLE")
    if configured and os.path.exists(configured):
        return True
    return shutil.which("blender") is not None


requires_blender = pytest.mark.skipif(
    not blender_available(),
    reason="Blender not available; set BLENDER_EXECUTABLE to run rig integration tests",
)
