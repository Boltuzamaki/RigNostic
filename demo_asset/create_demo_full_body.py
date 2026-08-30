"""Generate a simple full-body character with RigNostic facial controls."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import create_demo_face as face  # noqa: E402


def capsule(name, location, scale, mat):
    return face.uv_sphere(name, location, scale, mat, 40, 24)


def main() -> None:
    # Build the tested facial-control fixture first, then extend it without
    # changing the object and shape-key names used by analysis and repair.
    face.main()

    skin = bpy.data.materials["Skin"]
    shirt = face.material("Shirt", (0.025, 0.19, 0.32, 1), roughness=0.55)
    trousers = face.material("Trousers", (0.025, 0.04, 0.075, 1), roughness=0.72)
    shoes = face.material("Shoes", (0.012, 0.014, 0.02, 1), roughness=0.45)
    accent = face.material("Shirt accent", (0.08, 0.72, 0.78, 1), metallic=0.05, roughness=0.4)

    capsule("Torso", (0, 0.18, -2.45), (0.92, 0.48, 1.25), shirt)
    capsule("Waist", (0, 0.19, -3.35), (0.68, 0.41, 0.55), trousers)
    capsule("ChestAccent", (0, -0.31, -2.25), (0.25, 0.035, 0.33), accent)
    for side, x in (("L", -1.0), ("R", 1.0)):
        capsule(f"UpperArm_{side}", (x, 0.18, -2.45), (0.30, 0.31, 0.92), shirt)
        capsule(f"Forearm_{side}", (x, 0.12, -3.35), (0.25, 0.27, 0.82), skin)
        capsule(f"Hand_{side}", (x, 0.05, -4.08), (0.28, 0.20, 0.36), skin)
        capsule(f"Leg_{side}", (x * 0.43, 0.2, -4.30), (0.39, 0.40, 1.25), trousers)
        capsule(f"Shoe_{side}", (x * 0.43, -0.08, -5.40), (0.43, 0.65, 0.28), shoes)

    rig = bpy.data.objects["DemoFaceRig"]
    rig.name = "DemoCharacterRig"
    rig.data.name = "DemoCharacterRigData"
    bpy.context.scene["rignostic_fixture"] = "demo_full_body_v1"
    bpy.context.scene["rignostic_example"] = "simple_full_body"

    camera = bpy.data.objects.get("DemoCamera")
    camera.location = (0, -12.8, -2.0)
    direction = Vector((0, 0, -2.0)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 58

    destination = face.output_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), check_existing=False)
    print(f"RIGNOSTIC_FULL_BODY_SAVED={destination}")


if __name__ == "__main__":
    main()
