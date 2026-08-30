from pathlib import Path

import pytest

from rignostic.repair.pipeline import RepairError, heal_rig, plan_repairs


def test_heal_rejects_overwriting_input(tmp_path: Path) -> None:
    target = tmp_path / "target.blend"
    reference = tmp_path / "reference.blend"
    with pytest.raises(RepairError, match="output must differ"):
        heal_rig(target, reference, target)


def test_plan_rejects_missing_input(tmp_path: Path) -> None:
    with pytest.raises(RepairError, match="target Blender file does not exist"):
        plan_repairs(tmp_path / "missing.blend", tmp_path / "reference.blend")


def test_plan_rejects_non_blend_input(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    reference = tmp_path / "reference.blend"
    target.touch()
    reference.touch()
    with pytest.raises(RepairError, match="target must be a .blend file"):
        plan_repairs(target, reference)
