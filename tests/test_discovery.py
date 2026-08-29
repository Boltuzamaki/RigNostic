import json
from pathlib import Path

from rignostic.discovery import build_inventory, call_discovery_tool
from rignostic.discovery.classifier import classify, side_for

RIG = Path("benchmark/clean_reference/rig.blend")


def test_all_discovery_list_tools() -> None:
    expected_nonempty = {
        "list_armatures", "list_bones", "list_shape_keys", "list_drivers",
        "list_constraints", "get_control_dependencies",
    }
    for operation in expected_nonempty:
        response = call_discovery_tool(RIG, operation)
        assert response["success"] is True
        assert response["result"]
    groups = call_discovery_tool(RIG, "list_vertex_groups")
    assert groups == {"success": True, "result": []}


def test_targeted_discovery_tools() -> None:
    shape = call_discovery_tool(RIG, "get_shape_key_info", name="jawOpen")
    assert shape["result"][0]["vertex_delta_summary"]["affected_vertex_count"] > 0
    driver = call_discovery_tool(RIG, "get_driver_info", name="jawOpen")
    assert driver["result"][0]["variables"][0]["targets"][0]["id"] == "FaceRig"
    constraint = call_discovery_tool(
        RIG, "get_constraint_info", owner="browUp_L", name="Brow Range"
    )
    assert len(constraint["result"]) == 1


def test_inventory_serialization_and_classification() -> None:
    inventory = build_inventory(RIG)
    payload = json.loads(json.dumps(inventory.to_dict()))
    assert payload["metadata"]["objects_scanned"] == 2
    assert not payload["warnings"]
    controls = {item["name"]: item for item in payload["likely_facial_controls"]}
    assert controls["mouthSmile_L"]["control_type"] == "smile"
    assert controls["mouthSmile_L"]["side"] == "left"
    assert controls["mouthSmile_L"]["confidence"] == 0.9


def test_side_normalization_and_unknown() -> None:
    assert side_for("mouthSmile.L") == "left"
    assert side_for("R_brow") == "right"
    assert side_for("jaw") is None
    assert classify("mystery_ctrl", []).control_type == "unknown"
