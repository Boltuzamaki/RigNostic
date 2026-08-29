"""Evaluate saved baseline outputs after agent execution has finished."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from .evaluator import defect_matches, evaluate, load_gold, metrics_dict
from .schemas import AgentResult


def evaluate_saved(root: Path) -> dict[str, Any]:
    result_paths = sorted((root / "results" / "baseline" / "cases").glob("case_*.json"))
    results = [AgentResult.from_dict(json.loads(path.read_text())) for path in result_paths]
    gold_by_case = {}
    for path in sorted((root / "benchmark" / "cases").glob("case_*/gold.json")):
        case_id, defects = load_gold(path)
        gold_by_case[case_id] = defects
    metrics = evaluate(results, gold_by_case)
    cases = []
    for result in results:
        gold = gold_by_case[result.case_id]
        matched = sum(
            any(defect_matches(found, expected) for found in result.detected_defects)
            for expected in gold
        )
        cases.append(
            {
                "case_id": result.case_id,
                "gold_defects": len(gold),
                "matched_defects": matched,
                "predicted_defects": len(result.detected_defects),
                "passed": matched == len(gold),
            }
        )
    aggregate = {
        **metrics_dict(metrics),
        "cases_attempted": len(results),
        "average_agent_actions": mean(item.agent_actions for item in results),
        "average_runtime_seconds": mean(item.runtime_seconds for item in results),
        "total_runtime_seconds": sum(item.runtime_seconds for item in results),
        "model_calls": sum(item.model_calls for item in results),
        "input_tokens": sum(item.input_tokens or 0 for item in results),
        "output_tokens": sum(item.output_tokens or 0 for item in results),
        "approximate_cost_usd": None,
    }
    payload = {
        "stage": "baseline",
        "model": "gemini-3.5-flash-lite",
        "aggregate": aggregate,
        "cases": cases,
        "results": [item.to_dict() for item in results],
    }
    output = root / "results" / "baseline" / "results.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Stage 0 baseline results",
        "",
        f"Defect detection recall: {aggregate['defect_detection_recall']:.1%}",
        f"False positives: {aggregate['false_positives']}",
        f"Affected-control accuracy: {aggregate['affected_control_accuracy']:.1%}",
        f"Root-cause accuracy: {aggregate['root_cause_accuracy']:.1%}",
        "",
        "| Case | Gold | Matched | Predicted | Result |",
        "|---|---:|---:|---:|---|",
    ]
    lines.extend(
        f"| {case['case_id']} | {case['gold_defects']} | {case['matched_defects']} | "
        f"{case['predicted_defects']} | {'PASS' if case['passed'] else 'FAIL'} |"
        for case in cases
    )
    (root / "results" / "baseline" / "summary.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return payload
