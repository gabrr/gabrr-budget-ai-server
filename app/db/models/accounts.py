from __future__ import annotations

from decimal import Decimal

from app.db.models.base import TimestampModel


class Account(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    name: str
    type: str
    institution_name: str | None = None
    currency: str = "BRL"
    opening_balance: Decimal = Decimal("0.00")
    is_active: bool = True
