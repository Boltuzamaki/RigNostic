"""Deterministic Blender-side Structured Rig Discovery tools."""

import json
import sys

import bpy


def request():
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    result = {"operation": values[0] if values else "list_armatures"}
    for index in range(1, len(values), 2):
        result[values[index].removeprefix("--")] = values[index + 1]
    return result


def driver_rows():
    rows = []
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        animation = getattr(keys, "animation_data", None)
        for index, curve in enumerate(animation.drivers if animation else []):
            variables = []
            for variable in curve.driver.variables:
                targets = []
                for target in variable.targets:
                    targets.append(
                        {
                            "id": getattr(target.id, "name", None),
                            "data_path": target.data_path or None,
                            "bone_target": target.bone_target or None,
                            "transform_type": target.transform_type,
                            "transform_space": target.transform_space,
                        }
                    )
                variables.append({"name": variable.name, "type": variable.type, "targets": targets})
            rows.append(
                {
                    "id": f"{obj.name}:{curve.data_path}:{curve.array_index}:{index}",
                    "owner": obj.name,
                    "data_path": curve.data_path,
                    "array_index": curve.array_index,
                    "expression": curve.driver.expression,
                    "muted": curve.mute,
                    "variables": variables,
                }
            )
    return rows


def constraint_settings(value):
    names = (
        "use_limit_x", "use_limit_y", "use_limit_z", "use_min_x", "use_min_y",
        "use_min_z", "use_max_x", "use_max_y", "use_max_z", "min_x", "min_y",
        "min_z", "max_x", "max_y", "max_z",
    )
    return {name: getattr(value, name) for name in names if hasattr(value, name)}


def constraint_rows():
    rows = []
    for rig in bpy.data.objects:
        if rig.type != "ARMATURE":
            continue
        for bone in rig.pose.bones:
            for constraint in bone.constraints:
                rows.append(
                    {
                        "id": f"{rig.name}:{bone.name}:{constraint.name}",
                        "armature": rig.name,
                        "owner": bone.name,
                        "name": constraint.name,
                        "type": constraint.type,
                        "influence": constraint.influence,
                        "muted": constraint.mute,
                        "target": getattr(getattr(constraint, "target", None), "name", None),
                        "settings": constraint_settings(constraint),
                    }
                )
    return rows


def armatures():
    active = bpy.context.view_layer.objects.active
    return [
        {
            "object_name": obj.name,
            "data_name": obj.data.name,
            "bone_count": len(obj.data.bones),
            "visible": obj.visible_get(),
            "active": obj == active,
        }
        for obj in bpy.data.objects if obj.type == "ARMATURE"
    ]


def bones():
    return [
        {
            "id": f"{rig.name}:{bone.name}", "name": bone.name, "armature": rig.name,
            "parent": bone.parent.name if bone.parent else None,
            "children": [child.name for child in bone.children], "use_deform": bone.use_deform,
            "constraint_count": len(rig.pose.bones[bone.name].constraints),
        }
        for rig in bpy.data.objects if rig.type == "ARMATURE" for bone in rig.data.bones
    ]


def shape_keys():
    objects = []
    driven = {(row["owner"], row["data_path"]) for row in driver_rows()}
    for obj in bpy.data.objects:
        keys = getattr(obj.data, "shape_keys", None)
        if not keys:
            continue
        items = []
        for key in keys.key_blocks:
            path = f'key_blocks["{key.name}"].value'
            items.append(
                {
                    "id": f"{obj.name}:{key.name}", "name": key.name, "object": obj.name,
                    "value": key.value, "slider_min": key.slider_min,
                    "slider_max": key.slider_max, "mute": key.mute,
                    "has_driver": (obj.name, path) in driven,
                }
            )
        objects.append({"object": obj.name, "shape_keys": items})
    return objects


def vertex_groups():
    return [
        {"object": obj.name, "vertex_groups": [{"name": group.name, "index": group.index}
        for group in obj.vertex_groups]}
        for obj in bpy.data.objects if obj.type == "MESH" and obj.vertex_groups
    ]


def shape_key_detail(name):
    matches = []
    for item in shape_keys():
        for key in item["shape_keys"]:
            if key["name"] != name and key["id"] != name:
                continue
            obj = bpy.data.objects[item["object"]]
            blocks = obj.data.shape_keys.key_blocks
            block, basis = blocks[key["name"]], blocks[0]
            deltas = [(block.data[i].co - basis.data[i].co).length for i in range(len(block.data))]
            matches.append(
                {**key, "relative_key": block.relative_key.name if block.relative_key else None,
                 "vertex_delta_summary": {"affected_vertex_count": sum(v > 1e-6 for v in deltas),
                 "max_displacement": max(deltas, default=0.0)}}
            )
    return matches


def dependencies():
    edges = []
    for driver in driver_rows():
        target_name = None
        if 'key_blocks["' in driver["data_path"]:
            target_name = driver["data_path"].split('key_blocks["', 1)[1].split('"]', 1)[0]
        driver_node = driver["id"]
        edges.append({"source_type": "driver", "source": driver_node, "relationship": "drives",
                      "target_type": "shape_key", "target": target_name,
                      "target_object": driver["owner"], "deterministic": True})
        for variable in driver["variables"]:
            for target in variable["targets"]:
                data_path = target["data_path"] or ""
                property_bone = None
                if 'pose.bones["' in data_path:
                    property_bone = data_path.split('pose.bones["', 1)[1].split('"]', 1)[0]
                source = target["bone_target"] or property_bone or data_path or target["id"]
                source_type = "bone" if target["bone_target"] or property_bone else "property"
                edges.append({"source_type": source_type, "source": source,
                              "source_object": target["id"], "relationship": "feeds",
                              "target_type": "driver", "target": driver_node,
                              "deterministic": True})
    for item in vertex_groups():
        for group in item["vertex_groups"]:
            edges.append({"source_type": "vertex_group", "source": group["name"],
                          "relationship": "belongs_to", "target_type": "mesh",
                          "target": item["object"], "deterministic": True})
    return edges


def main():
    data = request()
    operation = data["operation"]
    functions = {
        "list_armatures": armatures, "list_bones": bones, "list_shape_keys": shape_keys,
        "list_drivers": driver_rows, "list_constraints": constraint_rows,
        "list_vertex_groups": vertex_groups, "get_control_dependencies": dependencies,
    }
    if operation in functions:
        output = functions[operation]()
    elif operation == "get_shape_key_info":
        output = shape_key_detail(data.get("name", ""))
    elif operation == "get_driver_info":
        name = data.get("name", "")
        output = [row for row in driver_rows() if name in {row["id"], row["data_path"]}
                  or name in row["data_path"]]
    elif operation == "get_constraint_info":
        name, owner = data.get("name", ""), data.get("owner")
        output = [row for row in constraint_rows() if name in {row["id"], row["name"]}
                  and (not owner or row["owner"] == owner)]
    else:
        raise ValueError(f"unsupported discovery operation: {operation}")
    print("RIGNOSTIC_DISCOVERY_RESULT=" + json.dumps({"success": True, "result": output}))


if __name__ == "__main__":
    main()
