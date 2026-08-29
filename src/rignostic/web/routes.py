"""HTTP routes; all Blender work is delegated to application services."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from rignostic.blender.runner import detect_blender

pages = Blueprint("pages", __name__)
logger = logging.getLogger(__name__)


def service():
    return current_app.extensions["analysis_service"]


def result_for(run):
    if run.result_path and run.result_path.exists():
        return json.loads(run.result_path.read_text(encoding="utf-8"))
    return None


@pages.get("/")
def overview():
    config = current_app.extensions["rignostic_config"]
    return render_template("overview.html", blender=detect_blender(config.blender.executable))


@pages.route("/analyze", methods=["GET", "POST"])
def analyze():
    config = current_app.extensions["rignostic_config"]
    blender = detect_blender(config.blender.executable)
    if request.method == "GET":
        return render_template("analyze.html", blender=blender)
    if blender is None:
        logger.warning("upload_rejected reason=blender_unavailable")
        return render_template(
            "analyze.html",
            blender=None,
            error="Blender is unavailable. Configure BLENDER_EXECUTABLE before analysis.",
        ), 503
    upload = request.files.get("rig")
    if not upload or not upload.filename:
        logger.warning("upload_rejected reason=missing_file")
        return render_template("analyze.html", blender=blender, error="Choose a .blend file."), 400
    safe_name = secure_filename(upload.filename)
    if Path(safe_name).suffix.lower() != ".blend":
        logger.warning("upload_rejected reason=invalid_extension filename=%s", safe_name)
        return render_template(
            "analyze.html", blender=blender, error="Only .blend files are accepted."
        ), 400
    upload_dir = Path(current_app.config["RUN_ROOT"]) / "uploads" / uuid4().hex
    upload_dir.mkdir(parents=True)
    destination = upload_dir / "input.blend"
    upload.save(destination)
    logger.info("upload_saved filename=%s bytes=%s", safe_name, destination.stat().st_size)
    run = service().create(safe_name, destination)
    return redirect(url_for("pages.analysis", run_id=run.id))


@pages.get("/analysis/<run_id>")
def analysis(run_id: str):
    run = service().get(run_id)
    if run is None:
        abort(404)
    return render_template("analysis.html", run=run, result=result_for(run))


@pages.get("/analysis/<run_id>/events")
def events(run_id: str):
    run = service().get(run_id)
    if run is None:
        abort(404)
    return jsonify(run.public())


@pages.get("/analysis/<run_id>/preview")
def preview(run_id: str):
    run = service().get(run_id)
    if run is None or run.preview_path is None or not run.preview_path.exists():
        abort(404)
    return send_file(run.preview_path, mimetype="image/png", conditional=True)


@pages.get("/analysis/<run_id>/model")
def viewer_model(run_id: str):
    run = service().get(run_id)
    if run is None or run.viewer_path is None or not run.viewer_path.exists():
        abort(404)
    return send_file(run.viewer_path, mimetype="model/gltf-binary", conditional=True)


@pages.get("/controls/<run_id>")
def controls(run_id: str):
    run = service().get(run_id)
    if run is None:
        abort(404)
    return render_template("controls.html", run=run, result=result_for(run))


@pages.get("/issues/<run_id>")
def issues(run_id: str):
    run = service().get(run_id)
    if run is None:
        abort(404)
    return render_template("issues.html", run=run, result=result_for(run))


@pages.get("/trajectory/<run_id>")
def trajectory(run_id: str):
    run = service().get(run_id)
    if run is None:
        abort(404)
    return render_template("trajectory.html", run=run)


@pages.get("/benchmarks")
def benchmarks():
    path = Path(current_app.config["BENCHMARK_RESULTS"])
    results = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return render_template("benchmarks.html", results=results)
