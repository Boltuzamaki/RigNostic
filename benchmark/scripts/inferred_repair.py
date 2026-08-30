"""Infer and apply high-confidence repairs from a rig's internal conventions."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import bpy

SENTINEL = "RIGNOSTIC_INFERRED_REPAIR="
SHAPE_PATTERN = re.compile(r'key_blocks\["(.+?)"\]\.value')


def args() -> dict[str, str | bool]:
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


def control_path(name: str) -> str:
    return f'pose.bones["{name}"]["value"]'


def paired_name(name: str) -> str | None:
    replacements = (("_L", "_R"), ("_R", "_L"), (".L", ".R"), (".R", ".L"))
    for suffix, replacement in replacements:
        if name.endswith(suffix):
            return name[: -len(suffix)] + replacement
    return None


def shape_delta(block, basis):
    return [point.co - basis.data[index].co for index, point in enumerate(block.data)]


def affected_count(block, basis, epsilon: float = 1e-6) -> int:
    return sum(delta.length > epsilon for delta in shape_delta(block, basis))


def average_delta(block, basis):
    changed = [delta for delta in shape_delta(block, basis) if delta.length > 1e-6]
    if not changed:
        return (0.0, 0.0, 0.0)
    return tuple(sum(delta[axis] for delta in changed) / len(changed) for axis in range(3))


def diagnose() -> list[dict]:
    findings = []
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        animation = keys.animation_data if keys else None
        for curve in animation.drivers if animation else []:
            match = SHAPE_PATTERN.fullmatch(curve.data_path)
            if not match or len(curve.driver.variables) != 1:
                continue
            shape = match.group(1)
            variable = curve.driver.variables[0]
            if len(variable.targets) != 1 or variable.type != "SINGLE_PROP":
                continue
            target = variable.targets[0]
            if curve.mute:
                findings.append({"kind": "driver_mute", "control": shape, "before": True,
                                 "after": False, "confidence": 1.0})
            if curve.driver.expression.replace(" ", "") != variable.name:
                findings.append({"kind": "driver_expression", "control": shape,
                                 "before": curve.driver.expression, "after": variable.name,
                                 "confidence": 0.98})
            expected_path = control_path(shape)
            rigs = [
                rig
                for rig in bpy.data.objects
                if rig.type == "ARMATURE" and shape in rig.pose.bones
            ]
            if rigs and target.data_path != expected_path:
                findings.append({"kind": "driver_target", "control": shape,
                                 "before": target.data_path, "after": expected_path,
                                 "target_object": rigs[0].name, "confidence": 0.99})
        if keys and len(keys.key_blocks) > 2:
            blocks = [block for block in keys.key_blocks if block.name != "Basis"]
            maxima = Counter(round(block.slider_max, 6) for block in blocks)
            expected_max, count = maxima.most_common(1)[0]
            if count / len(blocks) >= 0.7:
                for block in blocks:
                    if round(block.slider_max, 6) != expected_max:
                        findings.append({"kind": "slider_max", "control": block.name,
                                         "before": block.slider_max, "after": expected_max,
                                         "confidence": count / len(blocks)})
    constraints = {}
    for rig in (obj for obj in bpy.data.objects if obj.type == "ARMATURE"):
        for bone in rig.pose.bones:
            base = re.sub(r"([._-]?)(L|R|left|right)$", "", bone.name, flags=re.IGNORECASE)
            for constraint in bone.constraints:
                key = (rig.name, base, constraint.name)
                constraints.setdefault(key, []).append((bone, constraint))
    for items in constraints.values():
        if len(items) != 2:
            continue
        influences = [round(item[1].influence, 6) for item in items]
        if influences[0] != influences[1] and 1.0 in influences:
            for bone, constraint in items:
                if round(constraint.influence, 6) != 1.0:
                    findings.append({"kind": "constraint_influence", "control": bone.name,
                                     "constraint": constraint.name, "before": constraint.influence,
                                     "after": 1.0, "confidence": 0.97})
    shapes = {}
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        if not keys:
            continue
        basis = keys.key_blocks.get("Basis") or keys.key_blocks[0]
        for block in keys.key_blocks:
            if block != basis:
                shapes[(obj.name, block.name)] = (obj, block, basis)
    for (owner, name), (_, block, basis) in shapes.items():
        counterpart = paired_name(name)
        if counterpart is None:
            continue
        count = affected_count(block, basis)
        if count == 0:
            donors = [
                (other_owner, other_block, other_basis)
                for (other_owner, other_name), (_, other_block, other_basis) in shapes.items()
                if other_name == counterpart
                and len(other_block.data) == len(block.data)
                and affected_count(other_block, other_basis) > 0
            ]
            if len(donors) == 1:
                donor_owner, _, _ = donors[0]
                findings.append(
                    {
                        "kind": "shape_key_copy",
                        "control": name,
                        "owner": owner,
                        "donor_owner": donor_owner,
                        "donor_control": counterpart,
                        "before": "0 affected vertices",
                        "after": f"deformation transferred from {counterpart}",
                        "confidence": 0.99,
                    }
                )
        pair = shapes.get((owner, counterpart))
        if pair is None or name > counterpart or "smile" not in name.lower():
            continue
        other_block, other_basis = pair[1], pair[2]
        own_z = average_delta(block, basis)[2]
        other_z = average_delta(other_block, other_basis)[2]
        if own_z * other_z < 0 and max(abs(own_z), abs(other_z)) > 0.01:
            donor, target = (name, counterpart) if own_z > other_z else (counterpart, name)
            findings.append(
                {
                    "kind": "shape_key_mirror",
                    "control": target,
                    "owner": owner,
                    "donor_control": donor,
                    "before": round(min(own_z, other_z), 6),
                    "after": round(max(own_z, other_z), 6),
                    "confidence": 0.97,
                }
            )
    return findings


def apply(findings: list[dict]) -> None:
    for finding in findings:
        control = finding["control"]
        if finding["kind"] == "slider_max":
            for obj in bpy.data.objects:
                keys = getattr(obj.data, "shape_keys", None)
                if keys and control in keys.key_blocks:
                    keys.key_blocks[control].slider_max = finding["after"]
        elif finding["kind"] == "shape_key_copy":
            target_keys = bpy.data.objects[finding["owner"]].data.shape_keys.key_blocks
            donor_keys = bpy.data.objects[finding["donor_owner"]].data.shape_keys.key_blocks
            target, target_basis = target_keys[control], target_keys.get("Basis") or target_keys[0]
            donor = donor_keys[finding["donor_control"]]
            donor_basis = donor_keys.get("Basis") or donor_keys[0]
            for index, point in enumerate(target.data):
                point.co = target_basis.data[index].co + (
                    donor.data[index].co - donor_basis.data[index].co
                )
        elif finding["kind"] == "shape_key_mirror":
            keys = bpy.data.objects[finding["owner"]].data.shape_keys.key_blocks
            basis = keys.get("Basis") or keys[0]
            target, donor = keys[control], keys[finding["donor_control"]]
            for index, point in enumerate(target.data):
                coordinate = basis.data[index].co
                donor_index = min(
                    range(len(basis.data)),
                    key=lambda candidate: (
                        basis.data[candidate].co.x + coordinate.x
                    ) ** 2
                    + (basis.data[candidate].co.y - coordinate.y) ** 2
                    + (basis.data[candidate].co.z - coordinate.z) ** 2,
                )
                delta = donor.data[donor_index].co - basis.data[donor_index].co
                point.co = (
                    coordinate.x - delta.x,
                    coordinate.y + delta.y,
                    coordinate.z + delta.z,
                )
        elif finding["kind"] == "constraint_influence":
            for rig in (obj for obj in bpy.data.objects if obj.type == "ARMATURE"):
                if control in rig.pose.bones:
                    constraint = rig.pose.bones[control].constraints[finding["constraint"]]
                    constraint.influence = finding["after"]
        else:
            for obj in bpy.data.objects:
                keys = getattr(obj.data, "shape_keys", None)
                animation = keys.animation_data if keys else None
                for curve in animation.drivers if animation else []:
                    match = SHAPE_PATTERN.fullmatch(curve.data_path)
                    if not match or match.group(1) != control:
                        continue
                    if finding["kind"] == "driver_mute":
                        curve.mute = False
                    elif finding["kind"] == "driver_expression":
                        curve.driver.expression = finding["after"]
                    elif finding["kind"] == "driver_target":
                        target = curve.driver.variables[0].targets[0]
                        target.id = bpy.data.objects[finding["target_object"]]
                        target.data_path = finding["after"]


def main() -> None:
    request = args()
    findings = diagnose()
    applied = bool(request["apply"] and request.get("output"))
    remaining = findings
    if applied:
        apply(findings)
        output = Path(str(request["output"])).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
        remaining = diagnose()
    print(SENTINEL + json.dumps({"status": "healed" if applied and not remaining else "review",
          "applied": applied, "repair_count": len(findings), "repairs": findings,
          "remaining_findings": remaining, "output": str(request.get("output") or "")},
          separators=(",", ":")))
    if applied and remaining:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
