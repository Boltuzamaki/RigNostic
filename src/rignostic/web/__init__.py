"""Flask application factory for RigNostic."""

import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager

from rignostic.config import load_config
from rignostic.database import User, db
from rignostic.logging import configure_logging
from rignostic.services.analysis import AnalysisService

login_manager = LoginManager()


def create_app(test_config: dict | None = None) -> Flask:
    configure_logging()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL", "postgresql+psycopg://rignostic:rignostic@127.0.0.1:5432/rignostic"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=250 * 1024 * 1024,
        RUN_ROOT=Path(os.getenv("RIGNOSTIC_RUN_ROOT", str(Path(app.instance_path) / "runs"))),
        BENCHMARK_RESULTS=Path("results/baseline/results.json"),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "pages.login"
    login_manager.login_message = "Log in to access your rig workspace."

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id)) if user_id.isdigit() else None

    with app.app_context():
        db.create_all()
    analysis_service = AnalysisService(Path(app.config["RUN_ROOT"]), app)
    app.extensions["analysis_service"] = analysis_service
    reloader_child = os.getenv("WERKZEUG_RUN_MAIN") == "true"
    production_process = os.getenv("RIGNOSTIC_DEBUG", "1") != "1"
    if not app.config.get("TESTING") and (reloader_child or production_process):
        analysis_service.recover_interrupted()
    app.extensions["rignostic_config"] = load_config()
    from .routes import pages

    app.register_blueprint(pages)
    return app
