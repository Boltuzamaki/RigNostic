"""Verify that only the declared demo defects differ from the clean asset."""

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent


def key_delta(object_name: str, key_name: str) -> list[tuple[float, float, float]]:
    obj = bpy.data.objects[object_name]
    keys = obj.data.shape_keys.key_blocks
    basis = keys["Basis"]
    return [tuple(key.co - basis.data[index].co) for index, key in enumerate(keys[key_name].data)]


def magnitude(values: list[tuple[float, float, float]]) -> float:
    lengths = (sum(component * component for component in value) ** 0.5 for value in values)
    return max(lengths, default=0)


def snapshot(path: Path) -> dict[str, list[tuple[float, float, float]]]:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {
        "eyeBlink_L": key_delta("Eye_L", "eyeBlink_L"),
        "eyeBlink_R": key_delta("Eye_R", "eyeBlink_R"),
        "mouthSmile_L": key_delta("Lips", "mouthSmile_L"),
        "mouthSmile_R": key_delta("Lips", "mouthSmile_R"),
        "mouthFunnel": key_delta("Lips", "mouthFunnel"),
        "jawOpen": key_delta("Lips", "jawOpen"),
        "browUp_L": key_delta("Brow_L", "browUp_L"),
        "browUp_R": key_delta("Brow_R", "browUp_R"),
    }


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    good = Path(args[0]).resolve() if args else ROOT / "rignostic_demo_face_v2.blend"
    bad = Path(args[1]).resolve() if len(args) > 1 else ROOT / "rignostic_demo_face_v2_broken.blend"
    clean = snapshot(good)
    broken = snapshot(bad)
    assert magnitude(broken["eyeBlink_L"]) < 1e-6
    assert magnitude(clean["eyeBlink_L"]) > 0.1
    assert magnitude(broken["jawOpen"]) > magnitude(clean["jawOpen"]) * 1.85
    assert max(value[2] for value in clean["mouthSmile_R"]) > 0
    assert min(value[2] for value in broken["mouthSmile_R"]) < 0
    changed = {name for name in clean if clean[name] != broken[name]}
    expected = {"eyeBlink_L", "mouthSmile_R", "jawOpen"}
    assert changed == expected, f"Unexpected changed controls: {sorted(changed ^ expected)}"
    print(f"RIGNOSTIC_DEMO_PAIR_VALID changed={','.join(sorted(changed))}")


if __name__ == "__main__":
    main()
