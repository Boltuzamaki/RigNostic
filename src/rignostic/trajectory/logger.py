"""Append-only JSONL logs with concise, non-chain-of-thought decisions."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


class TrajectoryLogger:
    def __init__(self, path: Path, case_id: str, stage: str = "baseline") -> None:
        self.path = path
        self.case_id = case_id
        self.stage = stage

    def log(self, event: str, **fields: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": self.stage,
            "case_id": self.case_id,
            "event": event,
            **fields,
        }
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")

