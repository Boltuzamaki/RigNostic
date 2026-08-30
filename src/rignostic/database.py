"""Database models for authenticated, persistent analysis runs."""

from __future__ import annotations

from datetime import UTC, datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def now() -> datetime:
    return datetime.now(UTC)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now)
    runs = db.relationship("RunRecord", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class RunRecord(db.Model):
    __tablename__ = "analysis_runs"
    id = db.Column(db.String(32), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING", index=True)
    current_step = db.Column(db.String(100), nullable=False, default="Queued")
    progress = db.Column(db.Integer, nullable=False, default=0)
    error = db.Column(db.Text)
    source_path = db.Column(db.Text, nullable=False)
    run_dir = db.Column(db.Text, nullable=False)
    result = db.Column(JSON)
    events = db.Column(JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, index=True)
    started_at = db.Column(db.DateTime(timezone=True))
    finished_at = db.Column(db.DateTime(timezone=True))
    user = db.relationship("User", back_populates="runs")


class RepairRecord(db.Model):
    __tablename__ = "repair_runs"
    id = db.Column(db.String(32), primary_key=True)
    analysis_id = db.Column(
        db.String(32), db.ForeignKey("analysis_runs.id"), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    report = db.Column(JSON, nullable=False)
    output_path = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now, index=True)
