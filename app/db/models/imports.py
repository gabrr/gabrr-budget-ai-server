from __future__ import annotations

from datetime import datetime

from app.db.models.base import TimestampModel


class Import(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    uploaded_file_id: str
    status: str = "uploaded"
    source_type: str
    progress: int = 0
    current_step: str | None = None
    error_message: str | None = None
    completed_at: datetime | None = None
    committed_at: datetime | None = None
    reverted_at: datetime | None = None
