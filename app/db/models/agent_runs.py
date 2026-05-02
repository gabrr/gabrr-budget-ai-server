from __future__ import annotations

from datetime import datetime
from typing import Any

from app.db.models.base import DbModel


class AgentRun(DbModel):
    id: str | None = None
    import_id: str
    uploaded_file_id: str
    agent_name: str
    model_name: str | None = None
    status: str = "running"
    input_payload_json: dict[str, Any] | None = None
    output_payload_json: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
