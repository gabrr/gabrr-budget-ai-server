from __future__ import annotations

from app.db.models.base import TimestampModel


class User(TimestampModel):
    id: str | None = None
    email: str | None = None
    display_name: str | None = None
