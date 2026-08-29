"""Host-side wrappers for deterministic Blender discovery operations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from rignostic.blender.runner import run_blender
from rignostic.config import load_config

SCRIPT = Path(__file__).resolve().parents[3] / "benchmark" / "scripts" / "discovery_tools.py"
SENTINEL = "RIGNOSTIC_DISCOVERY_RESULT="
OPERATIONS = {
    "list_armatures", "list_bones", "list_shape_keys", "list_drivers",
    "list_constraints", "list_vertex_groups", "get_shape_key_info",
    "get_driver_info", "get_constraint_info", "get_control_dependencies",
}
logger = logging.getLogger(__name__)


def call_discovery_tool(blend_file: Path, operation: str, **arguments: Any) -> dict[str, Any]:
    if operation not in OPERATIONS:
        raise ValueError(f"unsupported discovery operation: {operation}")
    extra = ["--", operation]
    for key, value in arguments.items():
        extra.extend([f"--{key}", str(value)])
    logger.info("discovery_start operation=%s file=%s", operation, blend_file.name)
    result = run_blender(
        blend_file, SCRIPT, executable=load_config().blender.executable, extra_args=extra
    )
    if result.exit_code:
        logger.error("discovery_failed operation=%s", operation)
        return {"success": False, "error_type": "BLENDER_ERROR",
                "message": result.stderr or result.stdout, "recoverable": True}
    line = next((value for value in result.stdout.splitlines() if value.startswith(SENTINEL)), None)
    if not line:
        return {"success": False, "error_type": "INVALID_OUTPUT",
                "message": "Blender returned no structured discovery result", "recoverable": True}
    output = json.loads(line.removeprefix(SENTINEL))
    logger.debug("discovery_output operation=%s output=%s", operation, output)
    return output
