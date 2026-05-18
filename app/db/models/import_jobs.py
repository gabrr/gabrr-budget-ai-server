from __future__ import annotations

from datetime import datetime

from app.db.models.base import DbModel, TimestampModel


class ImportJob(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    status: str = "pending"
    current_step: str | None = None
    source_type: str = "pdf"
    original_filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    storage_path: str | None = None
    file_hash: str | None = None
    idempotency_key: str | None = None
    agent_input_payload_json: dict | None = None
    agent_output_payload_json: dict | None = None
    attempts: int = 0
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


class ImportJobPublic(DbModel):
    job_id: str
    status: str
    current_step: str | None = None
    error_message: str | None = None
    status_url: str
    events_url: str
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
