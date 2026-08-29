"""Small dependency-free loader for the fixed Stage 0 configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class BlenderConfig:
    executable: str = "blender"


@dataclass(frozen=True)
class BaselineConfig:
    provider: str = "auto"
    model: str = "gemini-3.5-flash-lite"
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
        values[f"{section}.{key}"] = value.strip().strip("\"'")
    return values


def load_config(path: Path | str = Path("configs/default.yaml")) -> Config:
    load_dotenv(override=False)
    values = _flat_yaml(Path(path))
    executable = os.getenv("BLENDER_EXECUTABLE", values.get("blender.executable", "blender"))
    model = os.getenv("RIGNOSTIC_MODEL", values.get("baseline.model", "gemini-3.5-flash-lite"))
    provider = os.getenv("RIGNOSTIC_PROVIDER", values.get("baseline.provider", "auto"))
    return Config(
        blender=BlenderConfig(executable=executable),
        baseline=BaselineConfig(
            provider=provider,
            model=model,
            temperature=float(values.get("baseline.temperature", "0")),
            max_tool_calls=int(values.get("baseline.max_tool_calls", "15")),
            max_output_tokens=int(values.get("baseline.max_output_tokens", "2000")),
        ),
    )
