from io import BytesIO
from pathlib import Path

import pytest

from rignostic.services.analysis import AnalysisRun
from rignostic.web import create_app


class FakeService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs = {}

    def create(self, filename: str, source_path: Path, user_id=None) -> AnalysisRun:
        run = AnalysisRun(
            "test-run", filename, source_path, self.root / "test-run", user_id=user_id
        )
        self.runs[run.id] = run
        return run

    def get(self, run_id: str):
        return self.runs.get(run_id)


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "RUN_ROOT": tmp_path / "runs",
            "BENCHMARK_RESULTS": tmp_path / "missing-results.json",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    app.extensions["analysis_service"] = FakeService(tmp_path / "runs")
    return app


@pytest.fixture
def client(app):
    client = app.test_client()
    client.post(
        "/signup",
        data={"username": "tester", "email": "tester@example.com", "password": "password123"},
    )
    return client


def test_overview_and_analyze_render(client) -> None:
    landing = client.get("/")
    assert landing.status_code == 200
    assert b"Your character looks fine" in landing.data
    assert b"Open dashboard" in landing.data
    assert b"<aside" not in landing.data
    assert b"Technical transparency" not in landing.data
    assert b"Measured on known broken rigs" not in landing.data
    assert b"See what RigNostic sees" not in landing.data
    assert client.get("/dashboard").status_code == 200
    response = client.get("/analyze")
    assert response.status_code == 200
    assert b"Analyze Blender rig" in response.data
    repair = client.get("/repair")
    assert repair.status_code == 302
    assert repair.headers["Location"].endswith("/analyze")
    assert b"Repair + Compare" not in response.data


def test_public_landing_signup_login_and_logout(app) -> None:
    client = app.test_client()
    landing = client.get("/")
    assert landing.status_code == 200
    assert b"Your character looks fine" in landing.data
    assert client.get("/dashboard").status_code == 302
    response = client.post(
        "/signup",
        data={"username": "artist", "email": "artist@example.com", "password": "securepass"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Analysis runs" in response.data
    client.post("/logout")
    response = client.post(
        "/login", data={"identity": "artist", "password": "securepass"},
        follow_redirects=True,
    )
    assert b"Analysis runs" in response.data


def test_invalid_upload(client) -> None:
    response = client.post(
        "/analyze",
        data={"rig": (BytesIO(b"not blender"), "payload.py")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert b"Only .blend files" in response.data


def test_valid_upload_uses_server_filename(app, client, tmp_path) -> None:
    response = client.post(
        "/analyze",
        data={"rig": (BytesIO(b"BLENDER-v-test"), "artist-face.blend")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/analysis/test-run")
    run = app.extensions["analysis_service"].get("test-run")
    assert run.filename == "artist-face.blend"
    assert run.source_path.name == "input.blend"
    assert run.source_path.read_bytes() == b"BLENDER-v-test"
    assert tmp_path in run.source_path.parents


def test_demo_cta_starts_bundled_analysis(app, client) -> None:
    response = client.post("/demo")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/analysis/test-run")
    run = app.extensions["analysis_service"].get("test-run")
    assert run.filename == "rignostic_demo_full_body_v1_broken.blend"
    assert run.source_path.read_bytes().startswith(b"BLENDER")


def test_unknown_run_is_404(client) -> None:
    assert client.get("/analysis/unknown").status_code == 404
    assert client.get("/repair/unknown").status_code == 404


def test_repair_comparison_renders_models(client, tmp_path) -> None:
    run_id = "a" * 32
    run_dir = tmp_path / "runs" / "repairs" / run_id
    run_dir.mkdir(parents=True)
    payload = {
        "run_id": run_id,
        "user_id": 1,
        "filename": "broken.blend",
        "report": {
            "repair_count": 1,
            "repairs": [{
                "category": "shape_keys", "identity": "FaceMesh:mouthSmile_R",
                "field": "coordinates", "before": [[0, 0, 0]], "after": [[0, 0, 1]],
            }],
        },
    }
    (run_dir / "report.json").write_text(__import__("json").dumps(payload))
    (run_dir / "before.glb").write_bytes(b"glTF")
    (run_dir / "after.glb").write_bytes(b"glTF")
    response = client.get(f"/repair/{run_id}")
    assert response.status_code == 200
    assert b"Before and after" in response.data
    assert b"mouthSmile_R" in response.data
    assert response.data.count(b"data-compare-viewer") == 2
    assert client.get(f"/repair/{run_id}/model/before").status_code == 200
    (run_dir / "after.blend").write_bytes(b"BLENDER")
    download = client.get(f"/repair/{run_id}/download")
    assert download.status_code == 200
    assert download.headers["Content-Disposition"].startswith("attachment;")


def test_completed_analysis_has_integrated_repair_action(app, client, tmp_path) -> None:
    service = app.extensions["analysis_service"]
    run_dir = tmp_path / "complete"
    run_dir.mkdir()
    run = AnalysisRun("complete", "face.blend", tmp_path / "face.blend", run_dir)
    run.status = "COMPLETE"
    run.progress = 100
    run.result_path = run_dir / "result.json"
    run.result_path.write_text(
        '{"findings":[],"model_calls":1,"input_tokens":0,"output_tokens":0}'
    )
    service.runs[run.id] = run
    response = client.get("/analysis/complete")
    assert response.status_code == 200
    assert b"Repair this run" in response.data
    assert b'action="/analysis/complete/repair"' in response.data


def test_run_detail_pages_have_shared_navigation(app, client, tmp_path) -> None:
    service = app.extensions["analysis_service"]
    run_dir = tmp_path / "navigation"
    run_dir.mkdir()
    run = AnalysisRun("navigation", "face.blend", tmp_path / "face.blend", run_dir)
    run.status = "COMPLETE"
    run.result_path = run_dir / "result.json"
    run.result_path.write_text(
        '{"bones":[],"shape_keys":[],"findings":[],"model_calls":1}'
    )
    service.runs[run.id] = run

    for path in ("controls", "issues", "trajectory"):
        response = client.get(f"/{path}/{run.id}")
        assert response.status_code == 200
        assert b"Back to analysis" in response.data
        assert b"Controls" in response.data
        assert b"Findings" in response.data
        assert b"Agent trajectory" in response.data


def test_analysis_failure_renders(app, client, tmp_path) -> None:
    service = app.extensions["analysis_service"]
    run = AnalysisRun("failed", "broken.blend", tmp_path / "broken.blend", tmp_path)
    run.status = "FAILED"
    run.error = "Blender could not open this file"
    service.runs[run.id] = run
    response = client.get("/analysis/failed")
    assert response.status_code == 200
    assert b"Blender could not open this file" in response.data
    assert b"js/analyze.js" not in response.data


def test_pending_analysis_includes_polling_script(app, client, tmp_path) -> None:
    service = app.extensions["analysis_service"]
    run = AnalysisRun("pending", "face.blend", tmp_path / "face.blend", tmp_path)
    service.runs[run.id] = run
    response = client.get("/analysis/pending")
    assert response.status_code == 200
    assert b"js/analyze.js" in response.data


def test_benchmark_page_without_results(client) -> None:
    response = client.get("/benchmarks")
    assert response.status_code == 200
    assert b"No baseline evaluation results exist" in response.data


def test_missing_blender_prerequisite(app, client, monkeypatch) -> None:
    monkeypatch.setattr("rignostic.web.routes.detect_blender", lambda _: None)
    response = client.get("/analyze")
    assert response.status_code == 200
    assert b"disabled" in response.data
    response = client.post(
        "/analyze",
        data={"rig": (BytesIO(b"BLENDER-v-test"), "face.blend")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503
