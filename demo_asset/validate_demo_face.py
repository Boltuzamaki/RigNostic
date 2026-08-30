"""Validate the generated RigNostic demo face inside Blender."""

import sys
from pathlib import Path

import bpy

EXPECTED = {
    "eyeBlink_L", "eyeBlink_R", "jawOpen", "mouthSmile_L",
    "mouthSmile_R", "mouthFunnel", "browUp_L", "browUp_R",
}


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    default_path = Path(__file__).with_name("rignostic_demo_face_v2.blend")
    path = Path(args[0] if args else default_path).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rig = bpy.data.objects.get("DemoFaceRig")
    if rig is None:
        rig = bpy.data.objects.get("DemoCharacterRig")
    assert rig and rig.type == "ARMATURE", "DemoFaceRig armature is missing"
    assert EXPECTED <= set(rig.pose.bones.keys()), "One or more control bones are missing"
    discovered = set()
    nonzero = set()
    driver_count = 0
    for obj in bpy.data.objects:
        keys = getattr(getattr(obj, "data", None), "shape_keys", None)
        if not keys:
            continue
        basis = keys.key_blocks[0]
        for key in keys.key_blocks[1:]:
            discovered.add(key.name)
            changed = any(
                (point.co - basis.data[index].co).length > 1e-5
                for index, point in enumerate(key.data)
            )
            if changed:
                nonzero.add(key.name)
        driver_count += len(keys.animation_data.drivers) if keys.animation_data else 0
    assert EXPECTED <= discovered, f"Missing shape keys: {sorted(EXPECTED - discovered)}"
    assert EXPECTED <= nonzero, f"Shape keys without deformation: {sorted(EXPECTED - nonzero)}"
    assert driver_count >= len(EXPECTED), "Expected driven shape keys"
    for object_name in ("MouthFill",):
        assert bpy.data.objects.get(object_name), f"{object_name} is missing"
    for control in EXPECTED:
        rig.pose.bones[control]["value"] = 1.0
    bpy.context.view_layer.update()
    print(f"RIGNOSTIC_DEMO_VALID controls={len(EXPECTED)} drivers={driver_count} path={path}")


if __name__ == "__main__":
    main()
