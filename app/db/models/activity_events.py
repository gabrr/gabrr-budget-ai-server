from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.models.base import DbModel


class ActivityEvent(DbModel):
    id: str | None = None
    user_id: str | None = None
    event_type: str
    entity_type: str
    entity_id: str
    import_id: str | None = None
    payload_json: dict[str, Any] | None = None
    undoable: bool = False
    undone_at: datetime | None = None
    created_at: datetime | None = None
