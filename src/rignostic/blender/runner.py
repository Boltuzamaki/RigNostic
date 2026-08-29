"""Invoke Blender headlessly without depending on GUI state."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


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
        is_executable = candidate.is_file() and os.access(candidate, os.X_OK)
        return candidate.resolve() if is_executable else None
    resolved = shutil.which(configured)
    return Path(resolved).resolve() if resolved else None


def run_blender(
    blend_file: Path | None = None,
    script: Path | None = None,
    *,
    executable: str | None = None,
    timeout_seconds: float = 120,
    extra_args: list[str] | None = None,
) -> BlenderRun:
    resolved = detect_blender(executable)
    if resolved is None:
        logger.error("blender_unavailable configured=%s", executable)
        raise BlenderUnavailableError(
            "Blender was not found. Install Blender 4.5.13 LTS and/or set "
            "BLENDER_EXECUTABLE to its executable path."
        )
    command = [str(resolved), "--background"]
    if blend_file is not None:
        command.append(str(blend_file))
    if script is not None:
        command.extend(["--python", str(script)])
    if extra_args:
        command.extend(extra_args)
    started = time.monotonic()
    logger.debug("blender_start command=%s timeout_seconds=%s", command, timeout_seconds)
    completed = subprocess.run(
        command, capture_output=True, text=True, timeout=timeout_seconds, check=False
    )
    exit_code = completed.returncode
    if (
        exit_code == 0
        and "Traceback (most recent call last):" in completed.stdout + completed.stderr
    ):
        exit_code = 1
    result = BlenderRun(
        command=tuple(command),
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=exit_code,
        runtime_seconds=time.monotonic() - started,
    )
    logger.info(
        "blender_complete exit_code=%s runtime_seconds=%.3f file=%s script=%s",
        result.exit_code,
        result.runtime_seconds,
        blend_file,
        script,
    )
    logger.debug("blender_stdout %s", result.stdout[-4000:])
    if result.stderr:
        logger.debug("blender_stderr %s", result.stderr[-4000:])
    return result
