"""Serializable baseline and gold-label schemas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Defect:
    defect_type: str
    affected_control: str
    root_cause: str
    description: str = ""
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        for name in ("defect_type", "affected_control", "root_cause"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Defect":
        return cls(
            defect_type=value["defect_type"],
            affected_control=value["affected_control"],
            root_cause=value.get("root_cause", value.get("likely_root_cause", "unknown")),
            description=value.get("description", ""),
            confidence=float(value.get("confidence", 1.0)),
        )


@dataclass
class AgentResult:
    case_id: str
    detected_defects: list[Defect] = field(default_factory=list)
    suggested_repairs: list[str] = field(default_factory=list)
    agent_actions: int = 0
    runtime_seconds: float = 0.0
    model_calls: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AgentResult":
        return cls(
            case_id=value["case_id"],
            detected_defects=[Defect.from_dict(item) for item in value.get("detected_defects", [])],
            suggested_repairs=list(value.get("suggested_repairs", [])),
            agent_actions=int(value.get("agent_actions", 0)),
            runtime_seconds=float(value.get("runtime_seconds", 0)),
            model_calls=int(value.get("model_calls", 0)),
            input_tokens=value.get("input_tokens"),
            output_tokens=value.get("output_tokens"),
        )

