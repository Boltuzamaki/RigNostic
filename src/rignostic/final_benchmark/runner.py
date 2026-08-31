"""Run the shipped adaptive agent over the fixed ten-case benchmark."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from rignostic.baseline.agent import analyze_rig_agent
from rignostic.blender.tools import call_basic_tool
from rignostic.config import Config
from rignostic.trajectory import TrajectoryLogger


def run_case(case_id: str, rig_path: Path, config: Config, root: Path) -> dict[str, Any]:
    """Run one case without exposing its gold label to the agent."""
    case_dir = root / "results" / "final_benchmark" / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    trajectory_path = case_dir / "trajectory.jsonl"
    trajectory_path.unlink(missing_ok=True)
    logger = TrajectoryLogger(trajectory_path, case_id, stage="final_benchmark")
    logger.log(
        "instruction",
        instruction_source="src/rignostic/baseline/agent.py",
        instruction=(
            "Select unused read-only Blender inspections from the fixed allowlist and report "
            "only defects supported by collected evidence."
        ),
    )
    logger.log("observation", observation="Received an unfamiliar Blender rig.")
    started = time.monotonic()

    def record(event: dict[str, Any]) -> None:
        event_type = str(event.get("type", "agent_event"))
        fields = {key: value for key, value in event.items() if key != "type"}
        logger.log(event_type, **fields)

    diagnosis, usage = analyze_rig_agent(
        rig_path,
        config.baseline,
        call_basic_tool,
        on_action=record,
    )
    runtime = time.monotonic() - started
    evidence = {
        key: value
        for key, value in diagnosis.items()
        if key not in {"detected_defects", "suggested_repairs", "findings", "trajectory"}
    }
    (case_dir / "evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    result = {
        "case_id": case_id,
        "detected_defects": diagnosis["detected_defects"],
        "suggested_repairs": diagnosis.get("suggested_repairs", []),
        "agent_actions": usage["model_calls"] + usage["tool_calls"],
        "runtime_seconds": runtime,
        **usage,
    }
    (case_dir / "agent_result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    logger.log(
        "final_output",
        final_output=result,
        runtime_seconds=runtime,
        model_usage=usage,
    )
    return result


def run_benchmark(root: Path, config: Config) -> list[dict[str, Any]]:
    """Run all cases from the immutable benchmark manifest."""
    manifest = json.loads((root / "benchmark" / "benchmark_manifest.json").read_text())
    results = []
    for case in manifest["cases"]:
        case_id = case["case_id"]
        result = run_case(case_id, root / "benchmark" / case["rig"], config, root)
        results.append(result)
        print(f"{case_id}: {len(result['detected_defects'])} finding(s)")
    return results
