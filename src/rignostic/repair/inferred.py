"""Reference-free, confidence-gated repair loop."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from rignostic.blender.runner import run_blender
from rignostic.config import load_config

from .pipeline import RepairError

SCRIPT = Path(__file__).resolve().parents[3] / "benchmark" / "scripts" / "inferred_repair.py"
SENTINEL = "RIGNOSTIC_INFERRED_REPAIR="


def _run(source: Path, output: Path | None = None) -> dict[str, Any]:
    if not source.is_file() or source.suffix.lower() != ".blend":
        raise RepairError(f"source must be an existing .blend file: {source}")
    arguments = []
    if output:
        arguments = ["--", "--apply", "--output", str(output)]
    result = run_blender(source, SCRIPT, executable=load_config().blender.executable,
                         extra_args=arguments)
    line = next((item for item in result.stdout.splitlines() if item.startswith(SENTINEL)), None)
    if result.exit_code != 0 or line is None:
        raise RepairError(result.stderr or result.stdout or "automatic repair failed")
    return json.loads(line.removeprefix(SENTINEL))


def plan_inferred(source: Path) -> dict[str, Any]:
    return _run(source.resolve())


def heal_inferred(source: Path, output: Path) -> dict[str, Any]:
    source, output = source.resolve(), output.resolve()
    if source == output:
        raise RepairError("output must differ from source")
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{output.stem}-", suffix=".blend",
                                               dir=output.parent)
    os.close(handle)
    temporary = Path(temporary_name)
    try:
        report = _run(source, temporary)
        if report["remaining_findings"]:
            raise RepairError("repair loop did not converge")
        os.replace(temporary, output)
        report["output"] = str(output)
        return report
    finally:
        temporary.unlink(missing_ok=True)
