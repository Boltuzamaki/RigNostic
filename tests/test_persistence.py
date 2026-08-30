from pathlib import Path

from rignostic.database import RunRecord, User, db
from rignostic.services.analysis import AnalysisService
from rignostic.web import create_app


class NoopThread:
    def __init__(self, **_kwargs):
        pass

    def start(self):
        pass


def test_run_is_persisted_and_reloaded(tmp_path: Path, monkeypatch) -> None:
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "RUN_ROOT": tmp_path / "runs",
        }
    )
    monkeypatch.setattr("rignostic.services.analysis.Thread", NoopThread)
    with app.app_context():
        user = User(username="artist", email="artist@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    source = tmp_path / "input.blend"
    source.write_bytes(b"BLENDER")
    service = AnalysisService(tmp_path / "runs", app)
    run = service.create("face.blend", source, user_id=user_id)
    with app.app_context():
        record = db.session.get(RunRecord, run.id)
        assert record is not None
        assert record.user_id == user_id
        assert record.progress == 0
        assert record.events == []
    reloaded = AnalysisService(tmp_path / "runs", app).get(run.id)
    assert reloaded is not None
    assert reloaded.filename == "face.blend"
    assert reloaded.user_id == user_id
