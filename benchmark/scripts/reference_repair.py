"""Plan or apply conservative repairs by comparing a rig with a trusted reference."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

SENTINEL = "RIGNOSTIC_REPAIR_RESULT="


def arguments() -> dict[str, str | bool]:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    result: dict[str, str | bool] = {"apply": False}
    index = 0
    while index < len(values):
        if values[index] == "--apply":
            result["apply"] = True
            index += 1
        else:
            result[values[index].removeprefix("--")] = values[index + 1]
            index += 2
    return result


def driver_key(owner: str, curve) -> str:
    return f"{owner}:{curve.data_path}:{curve.array_index}"


def snapshot(path: Path) -> dict:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    result = {"drivers": {}, "shape_keys": {}, "constraints": {}}
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        if keys:
            for block in keys.key_blocks:
                result["shape_keys"][f"{obj.name}:{block.name}"] = {
                    "owner": obj.name,
                    "name": block.name,
                    "slider_min": block.slider_min,
                    "slider_max": block.slider_max,
                    "coordinates": [list(point.co) for point in block.data],
                }
            animation = keys.animation_data
            for curve in animation.drivers if animation else []:
                variables = []
                for variable in curve.driver.variables:
                    variables.append(
                        {
                            "name": variable.name,
                            "type": variable.type,
                            "targets": [
                                {
                                    "id_name": target.id.name if target.id else None,
                                    "data_path": target.data_path,
                                    "bone_target": target.bone_target,
                                    "transform_type": target.transform_type,
                                    "transform_space": target.transform_space,
                                }
                                for target in variable.targets
                            ],
                        }
                    )
                result["drivers"][driver_key(obj.name, curve)] = {
                    "owner": obj.name,
                    "data_path": curve.data_path,
                    "array_index": curve.array_index,
                    "mute": curve.mute,
                    "expression": curve.driver.expression,
                    "variables": variables,
                }
        if obj.type == "ARMATURE":
            for bone in obj.pose.bones:
                for constraint in bone.constraints:
                    result["constraints"][f"{obj.name}:{bone.name}:{constraint.name}"] = {
                        "object": obj.name,
                        "bone": bone.name,
                        "name": constraint.name,
                        "influence": constraint.influence,
                        "mute": constraint.mute,
                    }
    return result


def differences(reference: dict, target: dict) -> list[dict]:
    repairs = []
    for category, fields in (
        ("drivers", ("mute", "expression", "variables")),
        ("shape_keys", ("slider_min", "slider_max", "coordinates")),
        ("constraints", ("influence", "mute")),
    ):
        for identity, expected in reference[category].items():
            actual = target[category].get(identity)
            if actual is None:
                continue
            for field in fields:
                if actual[field] != expected[field]:
                    repairs.append(
                        {
                            "category": category,
                            "identity": identity,
                            "field": field,
                            "before": actual[field],
                            "after": expected[field],
                        }
                    )
    return repairs


def topology_blockers(reference: dict, target: dict) -> list[dict[str, str]]:
    blockers = []
    for category in ("drivers", "shape_keys", "constraints"):
        missing = sorted(set(reference[category]) - set(target[category]))
        for identity in missing:
            blockers.append(
                {
                    "code": "MISSING_TOPOLOGY",
                    "category": category,
                    "identity": identity,
                    "message": f"Target is missing reference {category[:-1]} {identity}",
                }
            )
    return blockers


def apply_repairs(repairs: list[dict], reference: dict) -> None:
    for repair in repairs:
        expected = reference[repair["category"]][repair["identity"]]
        field = repair["field"]
        if repair["category"] == "shape_keys":
            block = bpy.data.objects[expected["owner"]].data.shape_keys.key_blocks[expected["name"]]
            if field == "coordinates":
                for point, coordinate in zip(block.data, expected[field], strict=True):
                    point.co = coordinate
            else:
                setattr(block, field, expected[field])
        elif repair["category"] == "constraints":
            bone = bpy.data.objects[expected["object"]].pose.bones[expected["bone"]]
            constraint = bone.constraints[expected["name"]]
            setattr(constraint, field, expected[field])
        else:
            keys = bpy.data.objects[expected["owner"]].data.shape_keys
            curve = next(
                item
                for item in keys.animation_data.drivers
                if item.data_path == expected["data_path"]
                and item.array_index == expected["array_index"]
            )
            if field != "variables":
                setattr(curve if field == "mute" else curve.driver, field, expected[field])
                continue
            while curve.driver.variables:
                curve.driver.variables.remove(curve.driver.variables[0])
            for variable_data in expected["variables"]:
                variable = curve.driver.variables.new()
                variable.name = variable_data["name"]
                variable.type = variable_data["type"]
                targets = zip(variable.targets, variable_data["targets"], strict=True)
                for target, target_data in targets:
                    target.id = bpy.data.objects.get(target_data["id_name"])
                    target.data_path = target_data["data_path"]
                    target.bone_target = target_data["bone_target"]
                    target.transform_type = target_data["transform_type"]
                    target.transform_space = target_data["transform_space"]


def main() -> None:
    args = arguments()
    reference_path = Path(str(args["reference"])).resolve()
    target_path = Path(str(args["target"])).resolve()
    output_path = Path(str(args["output"])).resolve() if args.get("output") else None
    reference = snapshot(reference_path)
    target = snapshot(target_path)
    blockers = topology_blockers(reference, target)
    repairs = differences(reference, target)
    applied = bool(args["apply"] and output_path and not blockers)
    if applied:
        apply_repairs(repairs, reference)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path), check_existing=False)
        remaining = differences(reference, snapshot(output_path))
    else:
        remaining = repairs
    result = {
        "status": "blocked" if blockers else ("healed" if applied and not remaining else "planned"),
        "applied": applied,
        "blockers": blockers,
        "repair_count": len(repairs),
        "repairs": repairs,
        "remaining_differences": len(remaining),
        "output": str(output_path) if applied else None,
    }
    print(SENTINEL + json.dumps(result, separators=(",", ":")))
    if blockers or (applied and remaining):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
