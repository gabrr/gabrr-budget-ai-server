from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.db.models.base import TimestampModel


class LearnedRule(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    rule_type: str
    match_pattern: str
    result_payload_json: dict[str, Any]
    confidence: Decimal | None = None
    source: str | None = None
    is_active: bool = True
