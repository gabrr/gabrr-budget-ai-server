from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.db.models.base import TimestampModel


class Budget(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    category_id: str
    account_id: str | None = None
    period_start: date
    period_end: date
    amount: Decimal
    currency: str = "BRL"
