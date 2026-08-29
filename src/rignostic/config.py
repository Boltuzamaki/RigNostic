"""Small dependency-free loader for the fixed Stage 0 configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BlenderConfig:
    executable: str = "blender"


@dataclass(frozen=True)
class BaselineConfig:
    model: str = "gpt-5-mini"
    temperature: float = 0.0
    max_tool_calls: int = 15
    max_output_tokens: int = 2000


@dataclass(frozen=True)
class Config:
    blender: BlenderConfig
    baseline: BaselineConfig


def _flat_yaml(path: Path) -> dict[str, str]:
    """Parse the simple two-level YAML used by this project."""
    values: dict[str, str] = {}
    section = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            continue
        key, separator, value = line.strip().partition(":")
        if not separator or not section:
            raise ValueError(f"Unsupported config line: {raw_line}")
        values[f"{section}.{key}"] = value.strip().strip('"\'')
    return values


def load_config(path: Path | str = Path("configs/default.yaml")) -> Config:
    values = _flat_yaml(Path(path))
    executable = os.getenv(
        "BLENDER_EXECUTABLE", values.get("blender.executable", "blender")
    )
    model = os.getenv("RIGNOSTIC_MODEL", values.get("baseline.model", "gpt-5-mini"))
    return Config(
        blender=BlenderConfig(executable=executable),
        baseline=BaselineConfig(
            model=model,
            temperature=float(values.get("baseline.temperature", "0")),
            max_tool_calls=int(values.get("baseline.max_tool_calls", "15")),
            max_output_tokens=int(values.get("baseline.max_output_tokens", "2000")),
        ),
    )

