"""Create ten deterministic defective variants from the clean reference."""

import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rig_spec import FACE_OBJECT, RIG_OBJECT, driver_path

ROOT = Path(__file__).resolve().parents[1]

GOLD = {
    "case_01": [("muted_driver", "eyeBlink_L", "driver_muted")],
    "case_02": [("excessive_multiplier", "jawOpen", "driver_multiplier_too_high")],
    "case_03": [("swapped_controls", "mouthSmile_L", "driver_targets_swapped")],
    "case_04": [("excessive_range", "mouthFunnel", "shape_key_slider_max")],
    "case_05": [("constraint_influence", "browUp_L", "constraint_influence_incorrect")],
    "case_06": [("reversed_direction", "jawOpen", "reversed_driver_sign")],
    "case_07": [("wrong_shape_key_target", "eyeBlink_R", "driver_targets_wrong_shape_key")],
    "case_08": [("excessive_deformation", "mouthSmile_R", "shape_key_geometry_excessive")],
    "case_09": [
        ("combination_overdeformation", "mouthSmile_L+mouthSmile_R", "corrective_shape_excessive")
    ],
    "case_10": [
        ("muted_driver", "browUp_R", "driver_muted"),
        ("constraint_influence", "browUp_R", "constraint_influence_incorrect"),
    ],
}


def fcurve(keys, shape):
    return next(
        item for item in keys.animation_data.drivers if item.data_path == driver_path(shape)
    )


def set_target(keys, shape: str, control: str) -> None:
    target = fcurve(keys, shape).driver.variables[0].targets[0]
    target.data_path = f'pose.bones["{control}"]["value"]'


def inject(case_id: str) -> None:
    face = bpy.data.objects[FACE_OBJECT]
    rig = bpy.data.objects[RIG_OBJECT]
    keys = face.data.shape_keys
    if case_id == "case_01":
        fcurve(keys, "eyeBlink_L").mute = True
    elif case_id == "case_02":
        fcurve(keys, "jawOpen").driver.expression = "var * 2"
    elif case_id == "case_03":
        set_target(keys, "mouthSmile_L", "mouthSmile_R")
        set_target(keys, "mouthSmile_R", "mouthSmile_L")
    elif case_id == "case_04":
        keys.key_blocks["mouthFunnel"].slider_max = 2.0
    elif case_id == "case_05":
        rig.pose.bones["browUp_L"].constraints["Brow Range"].influence = 0.2
    elif case_id == "case_06":
        fcurve(keys, "jawOpen").driver.expression = "-var"
    elif case_id == "case_07":
        set_target(keys, "mouthFunnel", "eyeBlink_R")
    elif case_id == "case_08":
        keys.key_blocks["mouthSmile_R"].data[7].co.z += 1.4
    elif case_id == "case_09":
        keys.key_blocks["smileCombination"].data[6].co.z += 1.8
    elif case_id == "case_10":
        fcurve(keys, "browUp_R").mute = True
        rig.pose.bones["browUp_R"].constraints["Brow Range"].influence = 0.0
    bpy.context.scene["rignostic_case"] = case_id


def main() -> None:
    reference = ROOT / "clean_reference" / "rig.blend"
    manifest = {"benchmark_version": 1, "reference": "clean_reference/rig.blend", "cases": []}
    for case_id, defects in GOLD.items():
        bpy.ops.wm.open_mainfile(filepath=str(reference))
        inject(case_id)
        directory = ROOT / "cases" / case_id
        directory.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(directory / "rig.blend"), check_existing=False)
        gold = {
            "case_id": case_id,
            "defects": [
                {
                    "defect_type": kind,
                    "affected_control": control,
                    "root_cause": cause,
                    "repairable": True,
                }
                for kind, control, cause in defects
            ],
        }
        (directory / "gold.json").write_text(json.dumps(gold, indent=2) + "\n", encoding="utf-8")
        manifest["cases"].append({"case_id": case_id, "rig": f"cases/{case_id}/rig.blend"})
    (ROOT / "benchmark_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("RIGNOSTIC_CASES_CREATED=10")


if __name__ == "__main__":
    main()
