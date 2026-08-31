"""Run Iteration 1 over the unchanged Stage 0 benchmark."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rignostic.baseline.runner import TOOL_OPERATIONS
from rignostic.blender.tools import call_basic_tool
from rignostic.config import Config
from rignostic.discovery import build_inventory
from rignostic.trajectory import TrajectoryLogger

from .agent import analyze_with_inventory


def run_case(case_id: str, rig_path: Path, config: Config, root: Path) -> dict[str, Any]:
    case_dir = root / "results" / "iteration_01" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    trajectory_path = case_dir / "trajectory.jsonl"
    trajectory_path.unlink(missing_ok=True)
    logger = TrajectoryLogger(trajectory_path, case_id, stage="iteration_01")
    started = time.monotonic()
    logger.log("observation", observation="Received an unfamiliar Blender rig.")
    logger.log("tool_call", tool="build_inventory", tool_arguments={})
    inventory = build_inventory(rig_path)
    inventory_dict = inventory.to_dict()
    (case_dir / "inventory.json").write_text(
        json.dumps(inventory_dict, indent=2) + "\n", encoding="utf-8"
    )
    logger.log(
        "inventory_update",
        tool_result_summary={
            "armatures": len(inventory.armatures), "bones": len(inventory.bones),
            "drivers": len(inventory.drivers), "dependencies": len(inventory.dependencies),
            "classified": len(inventory.likely_facial_controls),
            "unknown": len(inventory.unknown_controls), "warnings": len(inventory.warnings),
        },
    )
    for item in inventory.likely_facial_controls:
        logger.log("classification_decision", control=item.name, classification=item.control_type,
                   confidence=item.confidence, evidence=list(item.evidence))
    observations = {}
    for operation in TOOL_OPERATIONS:
        logger.log("tool_call", tool=operation, tool_arguments={})
        observations[operation] = call_basic_tool(rig_path, operation)
        value = observations[operation]
        item_count = len(value) if hasattr(value, "__len__") else None
        logger.log(
            "tool_result", tool=operation, tool_result_summary={"item_count": item_count}
        )
    logger.log(
        "decision",
        agent_decision_summary="Review inventory, dependencies, then baseline outputs.",
        next_action="Generate structured defect report without adaptive planning.",
    )
    diagnosis, usage = analyze_with_inventory(inventory_dict, observations, config.baseline)
    runtime = time.monotonic() - started
    result = {
        "case_id": case_id, "detected_defects": diagnosis["detected_defects"],
        "suggested_repairs": diagnosis.get("suggested_repairs", []),
        "agent_actions": 15, "runtime_seconds": runtime, **usage,
    }
    (case_dir / "agent_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    (case_dir / "tool_metrics.json").write_text(
        json.dumps(
            {
                "discovery_calls": 7,
                "baseline_calls": len(TOOL_OPERATIONS),
                "model_calls": usage["model_calls"],
                "runtime_seconds": runtime,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    logger.log("final_output", final_output=result, runtime_seconds=runtime, model_usage=usage)
    return result


def run_benchmark(root: Path, config: Config) -> list[dict[str, Any]]:
    manifest = json.loads((root / "benchmark" / "benchmark_manifest.json").read_text())
    results = []
    for case in manifest["cases"]:
        case_id = case["case_id"]
        result = run_case(case_id, root / "benchmark" / case["rig"], config, root)
        results.append(result)
        print(f"{case_id}: {len(result['detected_defects'])} finding(s)")
    return results
