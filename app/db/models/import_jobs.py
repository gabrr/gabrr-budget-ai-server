from __future__ import annotations

from datetime import datetime

from app.db.models.base import TimestampModel


class ImportJob(TimestampModel):
    id: str | None = None
    import_id: str
    status: str = "pending"
    attempts: int = 0
    locked_by: str | None = None
    locked_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
