"""Safe orchestration for reference-guided Blender repairs."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from rignostic.blender.runner import run_blender
from rignostic.config import load_config

SCRIPT = Path(__file__).resolve().parents[3] / "benchmark" / "scripts" / "reference_repair.py"
SENTINEL = "RIGNOSTIC_REPAIR_RESULT="


class RepairError(RuntimeError):
    """Raised when a repair cannot be safely completed and verified."""


def _run(target: Path, reference: Path, output: Path | None = None) -> dict[str, Any]:
    for label, path in (("target", target), ("reference", reference)):
        if not path.is_file():
            raise RepairError(f"{label} Blender file does not exist: {path}")
        if path.suffix.lower() != ".blend":
            raise RepairError(f"{label} must be a .blend file: {path}")
    args = ["--", "--target", str(target.resolve()), "--reference", str(reference.resolve())]
    if output is not None:
        args.extend(["--output", str(output.resolve()), "--apply"])
    result = run_blender(
        script=SCRIPT,
        executable=load_config().blender.executable,
        extra_args=args,
    )
    line = next(
        (item for item in result.stdout.splitlines() if item.startswith(SENTINEL)), None
    )
    if line is not None:
        payload = json.loads(line.removeprefix(SENTINEL))
        if payload.get("blockers"):
            messages = "; ".join(item["message"] for item in payload["blockers"])
            raise RepairError(f"incompatible rig topology: {messages}")
    if result.exit_code != 0 or line is None:
        raise RepairError(result.stderr or result.stdout or "Blender repair returned no result")
    return payload


def plan_repairs(target: Path, reference: Path) -> dict[str, Any]:
    """Return an immutable dry-run repair plan."""
    return _run(target, reference)


def heal_rig(target: Path, reference: Path, output: Path) -> dict[str, Any]:
    """Repair into a temporary file, verify it, then atomically publish the output."""
    target, reference, output = target.resolve(), reference.resolve(), output.resolve()
    if output in {target, reference}:
        raise RepairError("output must differ from both target and reference")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.stem}-", suffix=".blend", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        result = _run(target, reference, temporary)
        if result["remaining_differences"] != 0:
            raise RepairError("post-repair validation found remaining differences")
        os.replace(temporary, output)
        result["output"] = str(output)
        return result
    finally:
        temporary.unlink(missing_ok=True)
