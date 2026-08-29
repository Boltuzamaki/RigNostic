"""Validate the clean reference and every injected benchmark defect."""

import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_cases import GOLD, fcurve
from rig_spec import CONTROLS, FACE_OBJECT, RIG_OBJECT

ROOT = Path(__file__).resolve().parents[1]


def common_checks() -> list[str]:
    errors = []
    face = bpy.data.objects.get(FACE_OBJECT)
    rig = bpy.data.objects.get(RIG_OBJECT)
    if face is None:
        return ["missing FaceMesh"]
    if rig is None:
        return ["missing FaceRig"]
    keys = face.data.shape_keys
    missing_shapes = sorted(set(CONTROLS) - set(keys.key_blocks.keys()))
    missing_bones = sorted(set(CONTROLS) - set(rig.pose.bones.keys()))
    if missing_shapes:
        errors.append(f"missing shape keys: {missing_shapes}")
    if missing_bones:
        errors.append(f"missing bones: {missing_bones}")
    if len(keys.animation_data.drivers) != 9:
        errors.append("expected 9 drivers")
    return errors


def defect_present(case_id: str) -> bool:
    face, rig = bpy.data.objects[FACE_OBJECT], bpy.data.objects[RIG_OBJECT]
    keys = face.data.shape_keys
    checks = {
        "case_01": lambda: fcurve(keys, "eyeBlink_L").mute,
        "case_02": lambda: fcurve(keys, "jawOpen").driver.expression == "var * 2",
        "case_03": lambda: (
            "mouthSmile_R" in fcurve(keys, "mouthSmile_L").driver.variables[0].targets[0].data_path
        ),
        "case_04": lambda: keys.key_blocks["mouthFunnel"].slider_max == 2.0,
        "case_05": lambda: (
            abs(rig.pose.bones["browUp_L"].constraints["Brow Range"].influence - 0.2) < 1e-6
        ),
        "case_06": lambda: fcurve(keys, "jawOpen").driver.expression == "-var",
        "case_07": lambda: (
            "eyeBlink_R" in fcurve(keys, "mouthFunnel").driver.variables[0].targets[0].data_path
        ),
        "case_08": lambda: keys.key_blocks["mouthSmile_R"].data[7].co.z > 1.0,
        "case_09": lambda: keys.key_blocks["smileCombination"].data[6].co.z > 1.0,
        "case_10": lambda: (
            fcurve(keys, "browUp_R").mute
            and rig.pose.bones["browUp_R"].constraints["Brow Range"].influence == 0.0
        ),
    }
    return bool(checks[case_id]())


def main() -> None:
    report = {"reference": {}, "cases": []}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "clean_reference" / "rig.blend"))
    reference_errors = common_checks()
    report["reference"] = {"passed": not reference_errors, "errors": reference_errors}
    for case_id, expected in GOLD.items():
        path = ROOT / "cases" / case_id
        bpy.ops.wm.open_mainfile(filepath=str(path / "rig.blend"))
        errors = common_checks()
        gold = json.loads((path / "gold.json").read_text(encoding="utf-8"))
        gold_tuples = [
            (item["defect_type"], item["affected_control"], item["root_cause"])
            for item in gold["defects"]
        ]
        if gold_tuples != expected:
            errors.append("gold labels differ from generator specification")
        if bpy.context.scene.get("rignostic_case") != case_id:
            errors.append("case metadata mismatch")
        if not defect_present(case_id):
            errors.append("injected defect not present")
        report["cases"].append({"case_id": case_id, "passed": not errors, "errors": errors})
    report["passed"] = report["reference"]["passed"] and all(
        case["passed"] for case in report["cases"]
    )
    destination = ROOT / "validation_report.json"
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"RIGNOSTIC_BENCHMARK_VALID={report['passed']}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
