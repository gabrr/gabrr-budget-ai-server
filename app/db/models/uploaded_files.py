from __future__ import annotations

from app.db.models.base import TimestampModel


class UploadedFile(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    storage_path: str
    status: str = "stored"
