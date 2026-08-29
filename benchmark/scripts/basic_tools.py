"""Coarse JSON tools exposed to the Stage 0 general-purpose agent."""

import json
import sys

import bpy


def args():
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    result = {"operation": values[0] if values else "scene_summary"}
    for index in range(1, len(values), 2):
        result[values[index].removeprefix("--")] = values[index + 1]
    return result


def shape_keys():
    return {
        obj.name: list(obj.data.shape_keys.key_blocks.keys())
        for obj in bpy.data.objects
        if obj.type == "MESH" and obj.data.shape_keys
    }


def drivers():
    rows = []
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        animation = getattr(keys, "animation_data", None)
        for curve in animation.drivers if animation else []:
            rows.append(
                {
                    "owner": obj.name,
                    "data_path": curve.data_path,
                    "expression": curve.driver.expression,
                    "muted": curve.mute,
                }
            )
    return rows


def main():
    request = args()
    operation = request["operation"]
    if operation == "scene_summary":
        output = {
            "objects": len(bpy.data.objects),
            "types": {
                kind: sum(o.type == kind for o in bpy.data.objects) for kind in ("MESH", "ARMATURE")
            },
        }
    elif operation == "objects":
        output = [{"name": o.name, "type": o.type} for o in bpy.data.objects]
    elif operation == "basic_rig_info":
        output = {
            "armatures": sum(o.type == "ARMATURE" for o in bpy.data.objects),
            "meshes": sum(o.type == "MESH" for o in bpy.data.objects),
        }
    elif operation == "bone_names":
        output = {
            o.name: list(o.data.bones.keys()) for o in bpy.data.objects if o.type == "ARMATURE"
        }
    elif operation == "shape_key_names":
        output = shape_keys()
    elif operation == "driver_summary":
        output = drivers()
    elif operation == "constraint_summary":
        output = [
            {
                "owner": bone.name,
                "name": c.name,
                "type": c.type,
                "influence": c.influence,
                "mute": c.mute,
            }
            for rig in bpy.data.objects
            if rig.type == "ARMATURE"
            for bone in rig.pose.bones
            for c in bone.constraints
        ]
    elif operation in {"set_shape_key", "reset_shape_keys"}:
        for obj in bpy.data.objects:
            keys = getattr(obj.data, "shape_keys", None)
            if not keys:
                continue
            for key in keys.key_blocks:
                if operation == "reset_shape_keys" or key.name == request.get("name"):
                    key.value = 0.0 if operation == "reset_shape_keys" else float(request["value"])
        output = {"success": True, "operation": operation}
    else:
        raise ValueError(f"unsupported operation: {operation}")
    print("RIGNOSTIC_TOOL_RESULT=" + json.dumps(output, separators=(",", ":")))


if __name__ == "__main__":
    main()
