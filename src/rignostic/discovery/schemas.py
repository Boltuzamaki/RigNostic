"""Serializable Iteration 1 RigInventory schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ControlClassification:
    name: str
    control_type: str
    side: str | None
    confidence: float
    evidence: tuple[str, ...]
    original_name: str


@dataclass
class RigInventory:
    metadata: dict[str, Any]
    armatures: list[dict[str, Any]] = field(default_factory=list)
    bones: list[dict[str, Any]] = field(default_factory=list)
    shape_keys: list[dict[str, Any]] = field(default_factory=list)
    drivers: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    vertex_groups: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    likely_facial_controls: list[ControlClassification] = field(default_factory=list)
    unknown_controls: list[ControlClassification] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
