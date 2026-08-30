"""HTTP routes; all Blender work is delegated to application services."""

from __future__ import annotations

import json
import logging
import shutil
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
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from rignostic.blender.runner import detect_blender
from rignostic.blender.tools import call_basic_tool
from rignostic.database import RepairRecord, RunRecord, User, db
from rignostic.repair import RepairError, heal_inferred, plan_inferred

pages = Blueprint("pages", __name__)
logger = logging.getLogger(__name__)


def service():
    return current_app.extensions["analysis_service"]


def result_for(run):
    if run.result_path and run.result_path.exists():
        return json.loads(run.result_path.read_text(encoding="utf-8"))
    record = db.session.get(RunRecord, run.id)
    if record is not None:
        return record.result
    return None


def _blend_upload(name: str, destination: Path):
    upload = request.files.get(name)
    if not upload or not upload.filename:
        return None, f"Choose a {name.replace('_', ' ')} .blend file."
    safe_name = secure_filename(upload.filename)
    if Path(safe_name).suffix.lower() != ".blend":
        return None, f"The {name.replace('_', ' ')} must be a .blend file."
    upload.save(destination)
    return safe_name, None


@pages.get("/")
def overview():
    return render_template("landing.html")


@pages.post("/demo")
@login_required
def demo():
    source = Path(__file__).resolve().parents[3] / "demo_asset" / (
        "rignostic_demo_full_body_v1_broken.blend"
    )
    if not source.is_file():
        abort(503, "The bundled demo rig is unavailable.")
    upload_dir = Path(current_app.config["RUN_ROOT"]) / "uploads" / uuid4().hex
    upload_dir.mkdir(parents=True)
    destination = upload_dir / "input.blend"
    shutil.copy2(source, destination)
    run = service().create(source.name, destination, user_id=current_user.id)
    logger.info("demo_analysis_created run_id=%s", run.id)
    return redirect(url_for("pages.analysis", run_id=run.id))


@pages.get("/dashboard")
@login_required
def dashboard():
    config = current_app.extensions["rignostic_config"]
    runs = db.session.execute(
        db.select(RunRecord)
        .where(RunRecord.user_id == current_user.id)
        .order_by(RunRecord.created_at.desc())
    ).scalars().all()
    return render_template(
        "overview.html", blender=detect_blender(config.blender.executable), runs=runs
    )


@pages.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("pages.dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not (3 <= len(username) <= 40) or not username.replace("_", "").isalnum():
            error = "Username must be 3–40 letters, numbers, or underscores."
        elif "@" not in email or len(email) > 255:
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif db.session.scalar(
            db.select(User).where((User.email == email) | (User.username == username))
        ):
            error = "That email or username is already registered."
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("pages.dashboard"))
    return render_template("signup.html", error=error)


@pages.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("pages.dashboard"))
    error = None
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "")
        user = db.session.scalar(
            db.select(User).where((User.email == identity.lower()) | (User.username == identity))
        )
        if user is None or not user.check_password(password):
            error = "Invalid email/username or password."
        else:
            login_user(user)
            return redirect(url_for("pages.dashboard"))
    return render_template("login.html", error=error)


@pages.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("pages.overview"))


def owned_run(run_id: str):
    run = service().get(run_id)
    if run is None or run.user_id not in {None, current_user.id}:
        abort(404)
    return run


@pages.route("/analyze", methods=["GET", "POST"])
@login_required
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
    run = service().create(safe_name, destination, user_id=current_user.id)
    return redirect(url_for("pages.analysis", run_id=run.id))


@pages.get("/repair")
@login_required
def repair():
    return redirect(url_for("pages.analyze"))


def _repair_run(run_id: str) -> Path:
    if len(run_id) != 32 or any(character not in "0123456789abcdef" for character in run_id):
        abort(404)
    path = Path(current_app.config["RUN_ROOT"]) / "repairs" / run_id
    if not path.is_dir():
        abort(404)
    report_path = path / "report.json"
    if report_path.is_file():
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if payload.get("user_id") != current_user.id:
            abort(404)
    return path


def _repair_control(repair: dict) -> str:
    if "control" in repair:
        return repair["control"]
    identity = repair["identity"]
    if repair["category"] == "constraints":
        return identity.split(":")[-2]
    if repair["category"] == "shape_keys":
        return identity.split(":")[-1]
    quoted = identity.split('"')
    return quoted[1] if len(quoted) > 2 else identity


@pages.get("/repair/<run_id>")
@login_required
def repair_comparison(run_id: str):
    run_dir = _repair_run(run_id)
    report_path = run_dir / "report.json"
    if not report_path.is_file():
        abort(404)
    result = json.loads(report_path.read_text(encoding="utf-8"))
    changed_controls = sorted({_repair_control(item) for item in result["report"]["repairs"]})
    return render_template(
        "repair_comparison.html", result=result, changed_controls=changed_controls
    )


@pages.get("/repair/<run_id>/model/<version>")
@login_required
def repair_model(run_id: str, version: str):
    if version not in {"before", "after"}:
        abort(404)
    path = _repair_run(run_id) / f"{version}.glb"
    if not path.is_file():
        abort(404)
    return send_file(path, mimetype="model/gltf-binary", conditional=True)


@pages.get("/repair/<run_id>/download")
@login_required
def repair_download(run_id: str):
    path = _repair_run(run_id) / "after.blend"
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name="rignostic-healed.blend")


@pages.get("/analysis/<run_id>")
@login_required
def analysis(run_id: str):
    run = owned_run(run_id)
    repair_record = db.session.scalar(
        db.select(RepairRecord)
        .where(
            RepairRecord.analysis_id == run.id,
            RepairRecord.user_id == current_user.id,
        )
        .order_by(RepairRecord.created_at.desc())
    )
    repair_result = repair_record.report if repair_record else None
    changed_controls = (
        sorted({_repair_control(item) for item in repair_result["report"]["repairs"]})
        if repair_result
        else []
    )
    return render_template(
        "analysis.html", run=run, result=result_for(run), repair_result=repair_result,
        changed_controls=changed_controls, repair_error=request.args.get("repair_error"),
    )


@pages.post("/analysis/<run_id>/repair")
@login_required
def repair_analysis(run_id: str):
    run = owned_run(run_id)
    if run.status != "COMPLETE":
        abort(409)
    repair_id = uuid4().hex
    repair_dir = Path(current_app.config["RUN_ROOT"]) / "repairs" / repair_id
    repair_dir.mkdir(parents=True)
    try:
        plan = plan_inferred(run.source_path)
        if plan["repair_count"] == 0:
            return redirect(
                url_for(
                    "pages.analysis", run_id=run.id,
                    repair_error="No high-confidence automatic repair was found.",
                )
            )
        report = heal_inferred(run.source_path, repair_dir / "after.blend")
        call_basic_tool(run.source_path, "export_viewer", output=repair_dir / "before.glb")
        call_basic_tool(
            repair_dir / "after.blend", "export_viewer", output=repair_dir / "after.glb"
        )
    except (RepairError, RuntimeError) as repair_error:
        logger.exception("analysis_repair_failed run_id=%s repair_id=%s", run.id, repair_id)
        return redirect(
            url_for("pages.analysis", run_id=run.id, repair_error=str(repair_error))
        )
    payload = {
        "run_id": repair_id, "analysis_id": run.id, "user_id": current_user.id,
        "filename": run.filename, "plan": plan, "report": report,
    }
    (repair_dir / "report.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    db.session.add(
        RepairRecord(
            id=repair_id, analysis_id=run.id, user_id=current_user.id,
            status=report["status"], report=payload,
            output_path=str(repair_dir / "after.blend"),
        )
    )
    db.session.commit()
    return redirect(url_for("pages.analysis", run_id=run.id, repaired="1"))


@pages.get("/analysis/<run_id>/events")
@login_required
def events(run_id: str):
    run = owned_run(run_id)
    return jsonify(run.public())


@pages.get("/analysis/<run_id>/preview")
@login_required
def preview(run_id: str):
    run = owned_run(run_id)
    if run.preview_path is None or not run.preview_path.exists():
        abort(404)
    return send_file(run.preview_path, mimetype="image/png", conditional=True)


@pages.get("/analysis/<run_id>/model")
@login_required
def viewer_model(run_id: str):
    run = owned_run(run_id)
    if run.viewer_path is None or not run.viewer_path.exists():
        abort(404)
    return send_file(run.viewer_path, mimetype="model/gltf-binary", conditional=True)


@pages.get("/controls/<run_id>")
@login_required
def controls(run_id: str):
    run = owned_run(run_id)
    return render_template("controls.html", run=run, result=result_for(run))


@pages.get("/issues/<run_id>")
@login_required
def issues(run_id: str):
    run = owned_run(run_id)
    return render_template("issues.html", run=run, result=result_for(run))


@pages.get("/trajectory/<run_id>")
@login_required
def trajectory(run_id: str):
    run = owned_run(run_id)
    return render_template("trajectory.html", run=run)


@pages.get("/benchmarks")
def benchmarks():
    path = Path(current_app.config["BENCHMARK_RESULTS"])
    results = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return render_template("benchmarks.html", results=results)
