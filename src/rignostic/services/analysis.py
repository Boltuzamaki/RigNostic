"""Lightweight background runs for the current Stage 0 inspection capability."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from rignostic.baseline.agent import analyze_observations
from rignostic.blender.tools import call_basic_tool
from rignostic.config import load_config

logger = logging.getLogger(__name__)


@dataclass
class AnalysisRun:
    id: str
    filename: str
    source_path: Path
    run_dir: Path
    status: str = "PENDING"
    started_at: str | None = None
    finished_at: str | None = None
    current_step: str = "Queued"
    result_path: Path | None = None
    trajectory_path: Path | None = None
    preview_path: Path | None = None
    viewer_path: Path | None = None
    error: str | None = None
    events: list[dict[str, str]] = field(default_factory=list)

    def public(self) -> dict[str, Any]:
        value = asdict(self)
        for key in (
            "source_path",
            "run_dir",
            "result_path",
            "trajectory_path",
            "preview_path",
            "viewer_path",
        ):
            value.pop(key, None)
        return value


class AnalysisService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, AnalysisRun] = {}
        self._lock = Lock()

    def create(self, filename: str, source_path: Path) -> AnalysisRun:
        run_id = uuid4().hex
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True)
        run = AnalysisRun(run_id, filename, source_path, run_dir)
        run.result_path = run_dir / "result.json"
        run.trajectory_path = run_dir / "trajectory.jsonl"
        run.preview_path = run_dir / "preview.png"
        run.viewer_path = run_dir / "viewer.glb"
        with self._lock:
            self._runs[run_id] = run
        logger.info("analysis_created run_id=%s filename=%s", run_id, filename)
        Thread(target=self._execute, args=(run,), daemon=True).start()
        return run

    def get(self, run_id: str) -> AnalysisRun | None:
        return self._runs.get(run_id)

    def _event(self, run: AnalysisRun, step: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        run.current_step = step
        event = {"timestamp": timestamp, "step": step}
        run.events.append(event)
        logger.info("analysis_step run_id=%s step=%s", run.id, step)
        assert run.trajectory_path
        with run.trajectory_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"stage": "baseline", **event}) + "\n")

    def _execute(self, run: AnalysisRun) -> None:
        try:
            run.status = "RUNNING"
            run.started_at = datetime.now(UTC).isoformat()
            self._event(run, "Loading Blender")
            self._event(run, "Inspecting scene")
            scene = call_basic_tool(run.source_path, "scene_summary")
            self._event(run, "Reading controls")
            bones = call_basic_tool(run.source_path, "bone_names")
            shapes = call_basic_tool(run.source_path, "shape_key_names")
            drivers = call_basic_tool(run.source_path, "driver_summary")
            constraints = call_basic_tool(run.source_path, "constraint_summary")
            deformation = call_basic_tool(run.source_path, "shape_key_deformation_summary")
            observations = {
                "scene": scene,
                "bones": bones,
                "shape_keys": shapes,
                "drivers": drivers,
                "constraints": constraints,
                "shape_key_deformation": deformation,
            }
            self._event(run, "Rendering preview")
            assert run.preview_path
            call_basic_tool(run.source_path, "render_preview", output=run.preview_path)
            self._event(run, "Preparing interactive viewer")
            assert run.viewer_path
            call_basic_tool(run.source_path, "export_viewer", output=run.viewer_path)
            self._event(run, "Analyzing result")
            diagnosis, usage = analyze_observations(observations, load_config().baseline)
            self._event(run, "Generating report")
            result = {
                **observations,
                **diagnosis,
                "findings": diagnosis["detected_defects"],
                **usage,
            }
            assert run.result_path
            run.result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            run.status = "COMPLETE"
            run.current_step = "Complete"
            logger.info("analysis_complete run_id=%s findings=%s", run.id, len(result["findings"]))
        except Exception as error:  # background boundary: persist safe failure state
            run.status = "FAILED"
            run.error = str(error)
            run.current_step = "Failed"
            logger.exception("analysis_failed run_id=%s", run.id)
        finally:
            run.finished_at = datetime.now(UTC).isoformat()
