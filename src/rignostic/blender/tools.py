"""Python wrapper for the coarse Stage 0 Blender tool script."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rignostic.config import load_config

from .runner import run_blender

SCRIPT = Path(__file__).resolve().parents[3] / "benchmark" / "scripts" / "basic_tools.py"
SENTINEL = "RIGNOSTIC_TOOL_RESULT="


def call_basic_tool(blend_file: Path, operation: str, **arguments: Any) -> Any:
    extra = ["--", operation]
    for key, value in arguments.items():
        extra.extend([f"--{key}", str(value)])
    config = load_config()
    result = run_blender(
        blend_file,
        SCRIPT,
        executable=config.blender.executable,
        extra_args=extra,
    )
    if result.exit_code != 0:
        raise RuntimeError(result.stderr or result.stdout)
    line = next((line for line in result.stdout.splitlines() if line.startswith(SENTINEL)), None)
    if line is None:
        raise RuntimeError("Blender tool returned no structured result")
    return json.loads(line.removeprefix(SENTINEL))
