from __future__ import annotations

from datetime import UTC, datetime

from app.api.import_jobs_routes import import_job_event_key, import_job_to_public
from app.db.schemas.import_jobs import ImportJobSchema


def test_import_job_event_key_tracks_user_visible_timeline_fields() -> None:
    job = ImportJobSchema(
        id="job_1",
        user_id="user_1",
        status="processing",
        current_step="Reading PDF with agent",
        storage_path="/tmp/example.pdf",
        file_hash="abc",
        idempotency_key="idem",
    )

    first_key = import_job_event_key(job)
    job.current_step = "Validating transactions"
    changed_visible_event_key = import_job_event_key(job)
    job.finished_at = datetime.now(UTC)
    terminal_event_key = import_job_event_key(job)

    assert changed_visible_event_key != first_key
    assert terminal_event_key != changed_visible_event_key


def test_import_job_public_response_does_not_include_progress() -> None:
    now = datetime.now(UTC)
    job = ImportJobSchema(
        id="job_1",
        user_id="user_1",
        status="processing",
        current_step="Reading PDF with agent",
        storage_path="/tmp/example.pdf",
        file_hash="abc",
        idempotency_key="idem",
        created_at=now,
        updated_at=now,
    )

    payload = import_job_to_public(job).model_dump()

    assert "progress" not in payload
