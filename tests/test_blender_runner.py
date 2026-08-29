from pathlib import Path

from rignostic.blender.runner import detect_blender


def test_missing_explicit_blender_returns_none(tmp_path: Path) -> None:
    assert detect_blender(str(tmp_path / "missing-blender")) is None


def test_detects_executable(tmp_path: Path) -> None:
    executable = tmp_path / "blender"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    assert detect_blender(str(executable)) == executable.resolve()
