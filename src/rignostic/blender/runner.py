"""Invoke Blender headlessly without depending on GUI state."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import time


class BlenderUnavailableError(RuntimeError):
    """Raised when the configured Blender executable cannot be resolved."""


@dataclass(frozen=True)
class BlenderRun:
    command: tuple[str, ...]
    stdout: str
    stderr: str
    exit_code: int
    runtime_seconds: float


def detect_blender(executable: str | None = None) -> Path | None:
    configured = executable or os.getenv("BLENDER_EXECUTABLE", "blender")
    candidate = Path(configured).expanduser()
    if candidate.parent != Path("."):
        return candidate.resolve() if candidate.is_file() and os.access(candidate, os.X_OK) else None
    resolved = shutil.which(configured)
    return Path(resolved).resolve() if resolved else None


def run_blender(
    blend_file: Path | None = None,
    script: Path | None = None,
    *,
    executable: str | None = None,
    timeout_seconds: float = 120,
) -> BlenderRun:
    resolved = detect_blender(executable)
    if resolved is None:
        raise BlenderUnavailableError(
            "Blender was not found. Install Blender 4.3 LTS and/or set "
            "BLENDER_EXECUTABLE to its executable path."
        )
    command = [str(resolved), "--background"]
    if blend_file is not None:
        command.append(str(blend_file))
    if script is not None:
        command.extend(["--python", str(script)])
    started = time.monotonic()
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=timeout_seconds, check=False
    )
    return BlenderRun(
        command=tuple(command),
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
        runtime_seconds=time.monotonic() - started,
    )

