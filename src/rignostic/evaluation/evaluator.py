"""Transparent exact matching for baseline defect reports."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .schemas import AgentResult, Defect

ALIASES = {
    "driver muted": "muted_driver",
    "muted driver": "muted_driver",
    "wrong sign": "reversed_driver_sign",
}


def normalize(value: str) -> str:
    normalized = "_".join(value.strip().lower().replace("-", " ").split())
    return ALIASES.get(normalized.replace("_", " "), normalized)


def defect_matches(found: Defect, expected: Defect) -> bool:
    return all(
        normalize(left) == normalize(right)
        for left, right in (
            (found.defect_type, expected.defect_type),
            (found.affected_control, expected.affected_control),
            (found.root_cause, expected.root_cause),
        )
    )


@dataclass(frozen=True)
class Metrics:
    total_gold_defects: int
    correctly_detected: int
    false_positives: int
    defect_detection_recall: float


def evaluate(results: list[AgentResult], gold_by_case: dict[str, list[Defect]]) -> Metrics:
    correct = 0
    false_positives = 0
    for result in results:
        unmatched = list(gold_by_case.get(result.case_id, []))
        for found in result.detected_defects:
            match_index = next(
                (
                    index
                    for index, expected in enumerate(unmatched)
                    if defect_matches(found, expected)
                ),
                None,
            )
            if match_index is None:
                false_positives += 1
            else:
                correct += 1
                unmatched.pop(match_index)
    total = sum(len(items) for items in gold_by_case.values())
    return Metrics(total, correct, false_positives, correct / total if total else 0.0)


def load_gold(path: Path) -> tuple[str, list[Defect]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["case_id"], [Defect.from_dict(item) for item in payload["defects"]]


def metrics_dict(metrics: Metrics) -> dict[str, int | float]:
    return asdict(metrics)
