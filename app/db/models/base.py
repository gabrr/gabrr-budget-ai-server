from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DbModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class TimestampModel(DbModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
