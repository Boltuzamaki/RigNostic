"""Coarse JSON tools exposed to the Stage 0 general-purpose agent."""

import json
import sys

import bpy
from mathutils import Vector


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


def structural_details():
    driver_rows = []
    driven = set()
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        animation = getattr(keys, "animation_data", None)
        for curve in animation.drivers if animation else []:
            variables = []
            for variable in curve.driver.variables:
                variables.append(
                    {
                        "name": variable.name,
                        "targets": [
                            {
                                "id": getattr(target.id, "name", None),
                                "data_path": target.data_path or None,
                                "bone_target": target.bone_target or None,
                                "transform_type": target.transform_type,
                            }
                            for target in variable.targets
                        ],
                    }
                )
            row = {
                "owner": obj.name,
                "data_path": curve.data_path,
                "expression": curve.driver.expression,
                "muted": curve.mute,
                "variables": variables,
            }
            driver_rows.append(row)
            driven.add((obj.name, curve.data_path))
    key_rows = []
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        if not keys:
            continue
        for key in keys.key_blocks[1:]:
            path = f'key_blocks["{key.name}"].value'
            key_rows.append(
                {
                    "owner": obj.name,
                    "name": key.name,
                    "slider_min": key.slider_min,
                    "slider_max": key.slider_max,
                    "muted": key.mute,
                    "has_driver": (obj.name, path) in driven,
                }
            )
    constraint_rows = [
        {
            "owner": bone.name,
            "name": constraint.name,
            "type": constraint.type,
            "influence": constraint.influence,
            "muted": constraint.mute,
        }
        for rig in bpy.data.objects
        if rig.type == "ARMATURE"
        for bone in rig.pose.bones
        for constraint in bone.constraints
    ]
    return {"drivers": driver_rows, "shape_keys": key_rows, "constraints": constraint_rows}


def shape_key_deformation_summary():
    rows = []
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        if not keys:
            continue
        basis = keys.key_blocks[0]
        coordinates = [point.co for point in basis.data]
        bounds = Vector(
            max(point[axis] for point in coordinates)
            - min(point[axis] for point in coordinates)
            for axis in range(3)
        )
        object_extent = max(bounds, default=0.0)
        for key in keys.key_blocks[1:]:
            deltas = [
                key.data[index].co - basis.data[index].co
                for index in range(len(key.data))
            ]
            affected = [delta for delta in deltas if delta.length > 1e-6]
            average = sum(affected, Vector()) / len(affected) if affected else Vector()
            maximum = max((d.length for d in affected), default=0.0)
            rows.append(
                {
                    "owner": obj.name,
                    "shape_key": key.name,
                    "vertex_count": len(deltas),
                    "affected_vertex_count": len(affected),
                    "max_displacement": round(maximum, 6),
                    "relative_displacement": round(maximum / object_extent, 6)
                    if object_extent
                    else 0.0,
                    "average_delta": [round(value, 6) for value in average],
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
    elif operation == "structural_details":
        output = structural_details()
    elif operation == "shape_key_deformation_summary":
        output = shape_key_deformation_summary()
    elif operation == "render_preview":
        scene = bpy.context.scene
        if scene.camera is None:
            camera_data = bpy.data.cameras.new("RigNosticPreviewCamera")
            camera = bpy.data.objects.new("RigNosticPreviewCamera", camera_data)
            bpy.context.collection.objects.link(camera)
            camera.location = (0.0, -6.0, 0.0)
            direction = -camera.location
            camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            camera.data.lens = 52
            scene.camera = camera
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.render.resolution_x = 720
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = request["output"]
        scene.world.color = (0.025, 0.035, 0.05)
        bpy.ops.render.render(write_still=True)
        output = {"success": True, "format": "PNG"}
    elif operation == "export_viewer":
        bpy.ops.export_scene.gltf(
            filepath=request["output"],
            export_format="GLB",
            export_animations=False,
            export_morph=True,
            export_cameras=False,
            export_lights=False,
        )
        output = {"success": True, "format": "GLB"}
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
