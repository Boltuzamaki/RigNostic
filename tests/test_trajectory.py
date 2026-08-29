import json

from rignostic.trajectory import TrajectoryLogger


def test_jsonl_trajectory_record(tmp_path) -> None:
    path = tmp_path / "case_01.jsonl"
    TrajectoryLogger(path, "case_01").log("tool_call", tool="get_scene_summary", tool_arguments={})
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["stage"] == "baseline"
    assert record["case_id"] == "case_01"
    assert record["tool"] == "get_scene_summary"
