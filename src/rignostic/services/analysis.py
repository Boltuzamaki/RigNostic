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
from rignostic.database import RunRecord, db

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
    user_id: int | None = None
    progress: int = 0
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
    def __init__(self, root: Path, app=None) -> None:
        self.root = root
        self.app = app
        self.root.mkdir(parents=True, exist_ok=True)
        self._runs: dict[str, AnalysisRun] = {}
        self._lock = Lock()

    def create(self, filename: str, source_path: Path, user_id: int | None = None) -> AnalysisRun:
        run_id = uuid4().hex
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True)
        run = AnalysisRun(run_id, filename, source_path, run_dir, user_id=user_id)
        run.result_path = run_dir / "result.json"
        run.trajectory_path = run_dir / "trajectory.jsonl"
        run.preview_path = run_dir / "preview.png"
        run.viewer_path = run_dir / "viewer.glb"
        with self._lock:
            self._runs[run_id] = run
        self._persist(run)
        logger.info("analysis_created run_id=%s filename=%s", run_id, filename)
        Thread(target=self._execute, args=(run,), daemon=True).start()
        return run

    def get(self, run_id: str) -> AnalysisRun | None:
        run = self._runs.get(run_id)
        if run is not None or self.app is None:
            return run
        with self.app.app_context():
            record = db.session.get(RunRecord, run_id)
            if record is None:
                return None
            run = self._from_record(record)
            self._runs[run_id] = run
            return run

    @staticmethod
    def _from_record(record: RunRecord) -> AnalysisRun:
        run = AnalysisRun(
            id=record.id,
            filename=record.filename,
            source_path=Path(record.source_path),
            run_dir=Path(record.run_dir),
            status=record.status,
            current_step=record.current_step,
            error=record.error,
            user_id=record.user_id,
            progress=record.progress,
            events=list(record.events or []),
        )
        run.result_path = run.run_dir / "result.json"
        run.trajectory_path = run.run_dir / "trajectory.jsonl"
        run.preview_path = run.run_dir / "preview.png"
        run.viewer_path = run.run_dir / "viewer.glb"
        return run

    def recover_interrupted(self) -> int:
        """Resume database-backed work abandoned by a process restart."""
        if self.app is None:
            return 0
        with self.app.app_context():
            records = db.session.scalars(
                db.select(RunRecord).where(RunRecord.status.in_(("PENDING", "RUNNING")))
            ).all()
            runs = [self._from_record(record) for record in records]
        for run in runs:
            if not run.source_path.is_file():
                run.status = "FAILED"
                run.current_step = "Failed"
                run.error = "Analysis source file is missing after application restart."
                run.finished_at = datetime.now(UTC).isoformat()
                self._persist(run)
                continue
            run.status = "PENDING"
            run.current_step = "Recovering interrupted analysis"
            run.progress = 1
            run.error = None
            self._runs[run.id] = run
            self._persist(run)
            logger.warning("analysis_recovering run_id=%s", run.id)
            Thread(target=self._execute, args=(run,), daemon=True).start()
        return len(runs)

    def _persist(self, run: AnalysisRun, result: dict[str, Any] | None = None) -> None:
        if self.app is None or run.user_id is None:
            return
        with self.app.app_context():
            record = db.session.get(RunRecord, run.id)
            if record is None:
                record = RunRecord(
                    id=run.id, user_id=run.user_id, filename=run.filename,
                    source_path=str(run.source_path), run_dir=str(run.run_dir),
                )
                db.session.add(record)
            record.status = run.status
            record.current_step = run.current_step
            record.progress = run.progress
            record.error = run.error
            record.events = list(run.events)
            record.started_at = datetime.fromisoformat(run.started_at) if run.started_at else None
            record.finished_at = (
                datetime.fromisoformat(run.finished_at) if run.finished_at else None
            )
            if result is not None:
                record.result = result
            db.session.commit()

    def _event(self, run: AnalysisRun, step: str, progress: int) -> None:
        timestamp = datetime.now(UTC).isoformat()
        run.current_step = step
        run.progress = progress
        event = {"timestamp": timestamp, "step": step}
        run.events.append(event)
        logger.info("analysis_step run_id=%s step=%s", run.id, step)
        assert run.trajectory_path
        with run.trajectory_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"stage": "baseline", **event}) + "\n")
        self._persist(run)

    def _execute(self, run: AnalysisRun) -> None:
        try:
            run.status = "RUNNING"
            run.started_at = datetime.now(UTC).isoformat()
            self._event(run, "Loading Blender", 5)
            self._event(run, "Inspecting scene", 12)
            scene = call_basic_tool(run.source_path, "scene_summary")
            self._event(run, "Reading controls", 25)
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
            self._event(run, "Rendering preview", 55)
            assert run.preview_path
            call_basic_tool(run.source_path, "render_preview", output=run.preview_path)
            self._event(run, "Preparing interactive viewer", 68)
            assert run.viewer_path
            call_basic_tool(run.source_path, "export_viewer", output=run.viewer_path)
            self._event(run, "Analyzing result", 82)
            diagnosis, usage = analyze_observations(observations, load_config().baseline)
            self._event(run, "Generating report", 94)
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
            run.progress = 100
            self._persist(run, result)
            logger.info("analysis_complete run_id=%s findings=%s", run.id, len(result["findings"]))
        except Exception as error:  # background boundary: persist safe failure state
            run.status = "FAILED"
            run.error = str(error)
            run.current_step = "Failed"
            self._persist(run)
            logger.exception("analysis_failed run_id=%s", run.id)
        finally:
            run.finished_at = datetime.now(UTC).isoformat()
