from io import BytesIO
from pathlib import Path

import pytest

from rignostic.services.analysis import AnalysisRun
from rignostic.web import create_app


class FakeService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs = {}

    def create(self, filename: str, source_path: Path) -> AnalysisRun:
        run = AnalysisRun("test-run", filename, source_path, self.root / "test-run")
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
        }
    )
    app.extensions["analysis_service"] = FakeService(tmp_path / "runs")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_overview_and_analyze_render(client) -> None:
    assert client.get("/").status_code == 200
    response = client.get("/analyze")
    assert response.status_code == 200
    assert b"Analyze Blender rig" in response.data


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


def test_unknown_run_is_404(client) -> None:
    assert client.get("/analysis/unknown").status_code == 404


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
