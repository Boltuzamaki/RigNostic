"""Build and validate a compact RigInventory from discovery tools."""

from __future__ import annotations

import json
from pathlib import Path

from .classifier import classify
from .schemas import RigInventory
from .tools import call_discovery_tool


def _result(blend_file: Path, operation: str, warnings: list[dict[str, str]]):
    response = call_discovery_tool(blend_file, operation)
    if response.get("success"):
        return response["result"]
    warnings.append({"code": response.get("error_type", "UNKNOWN"),
                     "message": response.get("message", "Discovery failed")})
    return []


def build_inventory(blend_file: Path) -> RigInventory:
    warnings: list[dict[str, str]] = []
    armatures = _result(blend_file, "list_armatures", warnings)
    bones = _result(blend_file, "list_bones", warnings)
    shape_keys = _result(blend_file, "list_shape_keys", warnings)
    drivers = _result(blend_file, "list_drivers", warnings)
    constraints = _result(blend_file, "list_constraints", warnings)
    groups = _result(blend_file, "list_vertex_groups", warnings)
    dependencies = _result(blend_file, "get_control_dependencies", warnings)
    if not armatures:
        warnings.append({"code": "NO_ARMATURE", "message": "No armature was discovered"})
    evidence: dict[str, list[str]] = {}
    for edge in dependencies:
        if edge.get("source_type") == "bone" and edge.get("source"):
            evidence.setdefault(edge["source"], []).append(f"feeds driver {edge['target']}")
    names = {bone["name"] for bone in bones}
    names.update(
        key["name"]
        for item in shape_keys
        for key in item["shape_keys"]
        if key["name"] != "Basis"
    )
    classified = [classify(name, evidence.get(name, [])) for name in sorted(names)]
    identifiers = [item["id"] for item in bones] + [item["id"] for item in drivers]
    identifiers += [item["id"] for item in constraints]
    duplicate_ids = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if duplicate_ids:
        warnings.append(
            {"code": "DUPLICATE_IDS", "message": f"Duplicate IDs: {duplicate_ids}"}
        )
    driver_ids = {item["id"] for item in drivers}
    for edge in dependencies:
        if edge.get("target_type") == "driver" and edge.get("target") not in driver_ids:
            warnings.append(
                {
                    "code": "UNRESOLVED_DEPENDENCY",
                    "message": f"Missing driver target: {edge.get('target')}",
                }
            )
    inventory = RigInventory(
        metadata={
            "blend_file": str(blend_file),
            "blender_version": "4.5.13 LTS",
            "objects_scanned": len(bpy_objects(shape_keys, armatures)),
        },
        armatures=armatures, bones=bones, shape_keys=shape_keys, drivers=drivers,
        constraints=constraints, vertex_groups=groups, dependencies=dependencies,
        likely_facial_controls=[item for item in classified if item.control_type != "unknown"],
        unknown_controls=[item for item in classified if item.control_type == "unknown"],
        warnings=warnings,
    )
    json.dumps(inventory.to_dict())
    return inventory


def bpy_objects(shape_keys, armatures) -> set[str]:
    return {item["object"] for item in shape_keys} | {item["object_name"] for item in armatures}
