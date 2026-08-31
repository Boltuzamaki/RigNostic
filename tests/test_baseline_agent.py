"""Regression tests for the bounded diagnostic agent and evidence guards."""

import json
from pathlib import Path
from types import SimpleNamespace

from rignostic.baseline.agent import (
    _add_structural_findings,
    _remove_unsupported_driver_conflicts,
    analyze_rig_agent,
)
from rignostic.config import BaselineConfig


def finding(defect_type: str) -> dict[str, object]:
    return {
        "defect_type": defect_type,
        "affected_control": "jawOpen",
        "description": "claim",
        "likely_root_cause": "claim",
        "confidence": 0.95,
    }


def test_separate_shape_key_paths_are_not_driver_conflicts() -> None:
    result = {"detected_defects": [finding("Conflicting Drivers"), finding("Bad Range")]}
    observations = {
        "drivers": [
            {"owner": "Lips", "data_path": 'key_blocks["jawOpen"].value'},
            {"owner": "Lips", "data_path": 'key_blocks["mouthSmile_L"].value'},
        ]
    }

    filtered = _remove_unsupported_driver_conflicts(result, observations)

    assert [item["defect_type"] for item in filtered["detected_defects"]] == ["Bad Range"]


def test_exact_duplicate_driver_path_preserves_conflict_finding() -> None:
    result = {"detected_defects": [finding("Driver Conflict")]}
    driver = {"owner": "Lips", "data_path": 'key_blocks["jawOpen"].value'}

    filtered = _remove_unsupported_driver_conflicts(result, {"drivers": [driver, driver]})

    assert filtered["detected_defects"] == result["detected_defects"]


def test_structural_guard_adds_only_directly_supported_findings() -> None:
    report = {"detected_defects": [], "suggested_repairs": []}
    observations = {"shape_key_deformation": [
        {"owner": "Eye_L", "shape_key": "eyeBlink_L", "affected_vertex_count": 0,
         "relative_displacement": 0.0, "average_delta": [0.0, 0.0, 0.0]},
        {"owner": "Eye_R", "shape_key": "eyeBlink_R", "affected_vertex_count": 10,
         "relative_displacement": 0.3, "average_delta": [0.0, 0.0, 0.0]},
        {"owner": "Lips", "shape_key": "mouthSmile_L", "affected_vertex_count": 6,
         "relative_displacement": 0.24, "average_delta": [-0.08, 0.0, 0.27]},
        {"owner": "Lips", "shape_key": "mouthSmile_R", "affected_vertex_count": 6,
         "relative_displacement": 0.28, "average_delta": [0.12, 0.0, -0.30]},
        {"owner": "Lips", "shape_key": "mouthFunnel", "affected_vertex_count": 16,
         "relative_displacement": 0.27, "average_delta": [0.0, -0.16, 0.0]},
        {"owner": "Lips", "shape_key": "jawOpen", "affected_vertex_count": 16,
         "relative_displacement": 0.62, "average_delta": [0.0, 0.0, -0.36]},
    ]}

    guarded = _add_structural_findings(report, observations)

    actual = {
        (item["defect_type"], item["affected_control"])
        for item in guarded["detected_defects"]
    }
    assert actual == {
        ("zero_affected_vertices", "eyeBlink_L"),
        ("asymmetric_movement", "mouthSmile_R"),
        ("excessive_deformation", "jawOpen"),
    }
    assert all(
        item["evidence_source"] == "deterministic_validation"
        for item in guarded["detected_defects"]
    )


class FakeClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = iter(responses)

    def generate(self, _prompt: str):
        return SimpleNamespace(
            text=json.dumps(next(self.responses)), input_tokens=10, output_tokens=5
        )


def test_agent_selects_tools_then_reports(monkeypatch, tmp_path: Path) -> None:
    client = FakeClient([
        {"action": "use_tool", "tool": "shape_key_deformation_summary", "reason": "Check movement"},
        {"action": "use_tool", "tool": "driver_summary", "reason": "Trace the failed control"},
        {"action": "report", "detected_defects": [finding("Zero affected vertices")],
         "suggested_repairs": ["Restore from counterpart"]},
        {"action": "report", "detected_defects": [finding("Zero affected vertices")],
         "suggested_repairs": ["Restore from counterpart"]},
    ])
    monkeypatch.setattr("rignostic.baseline.agent.create_model_client", lambda _config: client)
    calls = []
    events = []

    def tool_runner(_source: Path, operation: str):
        calls.append(operation)
        if operation == "shape_key_deformation_summary":
            return [{"owner": "Eye_L", "shape_key": "eyeBlink_L",
                     "affected_vertex_count": 0, "relative_displacement": 0,
                     "average_delta": [0, 0, 0]}]
        if operation == "structural_details":
            return {"drivers": [], "shape_keys": [], "constraints": []}
        return [{"operation": operation}]

    result, usage = analyze_rig_agent(
        tmp_path / "rig.blend", BaselineConfig(), tool_runner, events.append
    )

    assert calls == ["shape_key_deformation_summary", "driver_summary", "structural_details"]
    assert usage["tool_calls"] == 3
    assert usage["model_calls"] == 4
    assert usage["provider"] == "gemini"
    assert result["findings"][0]["defect_type"] == "zero_affected_vertices"
    assert [event["type"] for event in events] == [
        "decision", "tool_result", "decision", "tool_result", "decision",
        "tool_result", "decision",
    ]


def test_agent_rejects_repeated_tool_without_running_it_twice(monkeypatch, tmp_path: Path) -> None:
    client = FakeClient([
        {"action": "use_tool", "tool": "driver_summary", "reason": "Read drivers"},
        {"action": "use_tool", "tool": "driver_summary", "reason": "Repeat"},
        {"action": "report", "detected_defects": [], "suggested_repairs": []},
        {"action": "report", "detected_defects": [], "suggested_repairs": []},
        {"action": "report", "detected_defects": [], "suggested_repairs": []},
    ])
    monkeypatch.setattr("rignostic.baseline.agent.create_model_client", lambda _config: client)
    calls = []
    events = []
    result, usage = analyze_rig_agent(
        tmp_path / "rig.blend",
        BaselineConfig(),
        lambda _source, operation: calls.append(operation) or [],
        events.append,
    )
    assert result["findings"] == []
    assert usage["tool_calls"] == 3
    assert calls == ["driver_summary", "structural_details", "shape_key_deformation_summary"]
    assert any(event["type"] == "rejected_action" for event in events)
