"""Flask application factory for RigNostic."""

from pathlib import Path

from flask import Flask

from rignostic.config import load_config
from rignostic.logging import configure_logging
from rignostic.services.analysis import AnalysisService


def create_app(test_config: dict | None = None) -> Flask:
    configure_logging()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="development-only-change-me",
        MAX_CONTENT_LENGTH=250 * 1024 * 1024,
        RUN_ROOT=Path(app.instance_path) / "runs",
        BENCHMARK_RESULTS=Path("results/baseline/results.json"),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.extensions["analysis_service"] = AnalysisService(Path(app.config["RUN_ROOT"]))
    app.extensions["rignostic_config"] = load_config()
    from .routes import pages

    app.register_blueprint(pages)
    return app
