from pathlib import Path

from rignostic.config import load_config


def test_load_default_config(monkeypatch) -> None:
    monkeypatch.delenv("BLENDER_EXECUTABLE", raising=False)
    config = load_config(Path("configs/default.yaml"))
    assert config.blender.executable == "blender"
    assert config.baseline.max_tool_calls == 15
    assert config.baseline.temperature == 0


def test_environment_overrides_blender(monkeypatch) -> None:
    monkeypatch.setenv("BLENDER_EXECUTABLE", "/example/blender")
    assert load_config().blender.executable == "/example/blender"

