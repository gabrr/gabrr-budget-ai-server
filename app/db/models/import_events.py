from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.models.base import DbModel


class ImportEvent(DbModel):
    id: str | None = None
    import_id: str
    event_type: str
    message: str | None = None
    progress: int | None = None
    payload_json: dict[str, Any] | None = None
    created_at: datetime | None = None
