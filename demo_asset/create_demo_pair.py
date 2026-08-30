"""Create a reproducible broken copy of the clean RigNostic demo face."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
GOOD = ROOT / "rignostic_demo_face_v2.blend"
BAD = ROOT / "rignostic_demo_face_v2_broken.blend"
MANIFEST = ROOT / "demo_pair_manifest.json"


def paths() -> tuple[Path, Path, Path]:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    good = Path(args[args.index("--good") + 1]).resolve() if "--good" in args else GOOD
    bad = Path(args[args.index("--bad") + 1]).resolve() if "--bad" in args else BAD
    manifest = (
        Path(args[args.index("--manifest") + 1]).resolve()
        if "--manifest" in args
        else MANIFEST
    )
    return good, bad, manifest


def main() -> None:
    good, bad, manifest = paths()
    if not good.exists():
        raise FileNotFoundError(f"Generate the clean demo first: {good}")
    bpy.ops.wm.open_mainfile(filepath=str(good))

    left_eye = bpy.data.objects["Eye_L"]
    blink = left_eye.data.shape_keys.key_blocks["eyeBlink_L"]
    basis = left_eye.data.shape_keys.key_blocks["Basis"]
    for index, point in enumerate(blink.data):
        point.co = basis.data[index].co

    lips = bpy.data.objects["Lips"]
    smile = lips.data.shape_keys.key_blocks["mouthSmile_R"]
    lip_basis = lips.data.shape_keys.key_blocks["Basis"]
    for index, point in enumerate(smile.data):
        point.co = lip_basis.data[index].co
        if index in {3, 4, 5, 11, 12, 13}:
            point.co += Vector((0.12, 0, -0.30))

    jaw = lips.data.shape_keys.key_blocks["jawOpen"]
    for index, point in enumerate(jaw.data):
        delta = point.co - lip_basis.data[index].co
        point.co = lip_basis.data[index].co + delta * 1.9

    fixture = "demo_full_body_v1_broken" if "full_body" in good.stem else "demo_face_v2_broken"
    bpy.context.scene["rignostic_fixture"] = fixture
    bpy.context.scene["rignostic_demo_defects"] = (
        "eyeBlink_L_no_deformation,mouthSmile_R_reversed,jawOpen_excessive"
    )
    bad.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(bad), check_existing=False)

    payload = {
        "good": good.name,
        "broken": bad.name,
        "defects": [
            {
                "defect_type": "missing_deformation",
                "affected_control": "eyeBlink_L",
                "expected": "left eye closes",
                "actual": "no vertex deformation",
            },
            {
                "defect_type": "reversed_direction",
                "affected_control": "mouthSmile_R",
                "expected": "right mouth corner rises",
                "actual": "right mouth corner moves downward",
            },
            {
                "defect_type": "excessive_range",
                "affected_control": "jawOpen",
                "expected": "controlled jaw opening",
                "actual": "lower lip displacement is 1.9 times the clean value",
            },
        ],
    }
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"RIGNOSTIC_DEMO_PAIR good={good} broken={bad} manifest={manifest}")


if __name__ == "__main__":
    main()
