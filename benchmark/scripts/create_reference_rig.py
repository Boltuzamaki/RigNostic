"""Generate the redistributable synthetic Stage 0 facial rig with Blender."""

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rig_spec import CONTROLS, FACE_OBJECT, RIG_OBJECT


def output_path() -> Path:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if "--output" in args:
        return Path(args[args.index("--output") + 1]).resolve()
    return Path(__file__).resolve().parents[1] / "clean_reference" / "rig.blend"


def add_shape(face, name: str, offsets: dict[int, tuple[float, float, float]]):
    key = face.shape_key_add(name=name, from_mix=False)
    for index, offset in offsets.items():
        base = face.data.vertices[index].co
        key.data[index].co = base + __import__("mathutils").Vector(offset)
    return key


def main() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    vertices = [
        (-1, -0.2, -1),
        (1, -0.2, -1),
        (-1, 0, 1),
        (1, 0, 1),
        (-0.65, -0.15, 0.3),
        (0.65, -0.15, 0.3),
        (-0.5, -0.2, -0.35),
        (0.5, -0.2, -0.35),
        (0, -0.25, -0.65),
        (0, -0.2, 0.65),
    ]
    mesh = bpy.data.meshes.new("FaceMeshData")
    mesh.from_pydata(vertices, [], [(0, 1, 3, 2)])
    face = bpy.data.objects.new(FACE_OBJECT, mesh)
    bpy.context.collection.objects.link(face)
    face.shape_key_add(name="Basis")
    shapes = {
        "eyeBlink_L": {4: (0, 0, -0.18)},
        "eyeBlink_R": {5: (0, 0, -0.18)},
        "jawOpen": {0: (0, 0, -0.35), 1: (0, 0, -0.35), 8: (0, 0, -0.4)},
        "mouthSmile_L": {6: (-0.12, 0, 0.2)},
        "mouthSmile_R": {7: (0.12, 0, 0.2)},
        "mouthFunnel": {6: (0.2, -0.1, 0), 7: (-0.2, -0.1, 0)},
        "browUp_L": {2: (0, 0, 0.18), 4: (0, 0, 0.12)},
        "browUp_R": {3: (0, 0, 0.18), 5: (0, 0, 0.12)},
        "smileCombination": {},
    }
    for name, offsets in shapes.items():
        add_shape(face, name, offsets)

    armature = bpy.data.armatures.new("FaceRigData")
    rig = bpy.data.objects.new(RIG_OBJECT, armature)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root = armature.edit_bones.new("face_root")
    root.head, root.tail = (0, 0, -1), (0, 0, 1)
    for index, name in enumerate(CONTROLS):
        bone = armature.edit_bones.new(name)
        bone.head = (-1.4 + index * 0.4, 0, -1.4)
        bone.tail = (bone.head.x, 0, -1.15)
        bone.parent = root
    bpy.ops.object.mode_set(mode="POSE")
    for name in CONTROLS:
        pose_bone = rig.pose.bones[name]
        pose_bone["value"] = 0.0
        ui = pose_bone.id_properties_ui("value")
        ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
    for name in ("browUp_L", "browUp_R"):
        constraint = rig.pose.bones[name].constraints.new("LIMIT_LOCATION")
        constraint.name = "Brow Range"
        constraint.use_min_z = True
        constraint.use_max_z = True
        constraint.min_z = 0.0
        constraint.max_z = 0.25
        constraint.owner_space = "LOCAL"
        constraint.influence = 1.0
    bpy.ops.object.mode_set(mode="OBJECT")

    for name in CONTROLS:
        fcurve = face.data.shape_keys.driver_add(f'key_blocks["{name}"].value')
        driver = fcurve.driver
        driver.type = "SCRIPTED"
        driver.expression = "var"
        variable = driver.variables.new()
        variable.name = "var"
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = rig
        variable.targets[0].data_path = f'pose.bones["{name}"]["value"]'

    combo = face.data.shape_keys.driver_add('key_blocks["smileCombination"].value').driver
    combo.type = "SCRIPTED"
    combo.expression = "max(0, left + right - 1)"
    for variable_name, control in (("left", "mouthSmile_L"), ("right", "mouthSmile_R")):
        variable = combo.variables.new()
        variable.name = variable_name
        variable.type = "SINGLE_PROP"
        variable.targets[0].id = rig
        variable.targets[0].data_path = f'pose.bones["{control}"]["value"]'

    bpy.context.scene["rignostic_fixture"] = "clean_reference_v1"
    bpy.context.scene["rignostic_case"] = "clean"
    destination = output_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), check_existing=False)
    print(f"RIGNOSTIC_REFERENCE_SAVED={destination}")


if __name__ == "__main__":
    main()
