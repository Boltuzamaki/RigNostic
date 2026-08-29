from pathlib import Path

from rignostic.blender.tools import call_basic_tool

RIG = Path("benchmark/clean_reference/rig.blend")


def test_reference_opens_and_basic_tools_execute() -> None:
    summary = call_basic_tool(RIG, "scene_summary")
    assert summary["types"] == {"MESH": 1, "ARMATURE": 1}
    names = call_basic_tool(RIG, "shape_key_names")
    assert "eyeBlink_L" in names["FaceMesh"]


def test_shape_key_can_be_changed_and_reset() -> None:
    assert call_basic_tool(RIG, "set_shape_key", name="eyeBlink_L", value=0.5)["success"]
    assert call_basic_tool(RIG, "reset_shape_keys")["success"]

