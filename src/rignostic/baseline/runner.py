"""Reproducible Stage 0 baseline execution over fixed benchmark rigs."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rignostic.baseline.agent import analyze_observations
from rignostic.blender.tools import call_basic_tool
from rignostic.config import Config
from rignostic.trajectory import TrajectoryLogger

TOOL_OPERATIONS = (
    "scene_summary",
    "basic_rig_info",
    "bone_names",
    "shape_key_names",
    "driver_summary",
    "constraint_summary",
)


def run_case(
    case_id: str,
    rig_path: Path,
    config: Config,
    trajectory_path: Path,
) -> dict[str, Any]:
    logger = TrajectoryLogger(trajectory_path, case_id)
    started = time.monotonic()
    observations: dict[str, Any] = {}
    logger.log("observation", observation="Received an unfamiliar Blender rig.")
    for operation in TOOL_OPERATIONS:
        logger.log("tool_call", tool=operation, tool_arguments={})
        value = call_basic_tool(rig_path, operation)
        observations[operation] = value
        count = len(value) if hasattr(value, "__len__") else None
        logger.log("tool_result", tool=operation, tool_result_summary={"item_count": count})
    logger.log(
        "decision",
        agent_decision_summary="Use the fixed baseline prompt to assess coarse tool outputs.",
        next_action="Generate structured defect report.",
    )
    diagnosis, usage = analyze_observations(observations, config.baseline)
    runtime = time.monotonic() - started
    result = {
        "case_id": case_id,
        "detected_defects": diagnosis["detected_defects"],
        "suggested_repairs": diagnosis.get("suggested_repairs", []),
        "agent_actions": len(TOOL_OPERATIONS) + 1,
        "runtime_seconds": runtime,
        **usage,
    }
    logger.log(
        "final_output",
        final_output=result,
        runtime_seconds=runtime,
        model_usage=usage,
    )
    return result


def run_benchmark(root: Path, config: Config) -> list[dict[str, Any]]:
    manifest = json.loads((root / "benchmark" / "benchmark_manifest.json").read_text())
    results_dir = root / "results" / "baseline" / "cases"
    trajectories_dir = root / "trajectories" / "baseline"
    results_dir.mkdir(parents=True, exist_ok=True)
    trajectories_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for case in manifest["cases"]:
        case_id = case["case_id"]
        trajectory = trajectories_dir / f"{case_id}.jsonl"
        trajectory.unlink(missing_ok=True)
        result = run_case(case_id, root / "benchmark" / case["rig"], config, trajectory)
        (results_dir / f"{case_id}.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        results.append(result)
        print(f"{case_id}: {len(result['detected_defects'])} finding(s)")
    return results
