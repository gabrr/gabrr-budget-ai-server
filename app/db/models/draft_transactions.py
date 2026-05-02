from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from app.db.models.base import TimestampModel


class DraftTransaction(TimestampModel):
    id: str | None = None
    import_id: str
    source_row_index: int | None = None
    account_id: str | None = None
    category_id: str | None = None
    posted_at: date | None = None
    description: str | None = Field(default=None, min_length=1)
    merchant_name: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    payment_method: str | None = None
    installments: int | None = None
    installments_current: int | None = None
    confidence: Decimal | None = None
    needs_review: bool = True
    review_reason: str | None = None
    duplicate_of_transaction_id: str | None = None
    status: str = "draft"
    raw_payload_json: dict[str, Any] | None = None
    committed_transaction_id: str | None = None

    @field_validator("amount", "confidence", mode="before")
    @classmethod
    def _as_decimal(cls, value: object) -> Decimal | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, Decimal):
            return value
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
            return Decimal(normalized) if normalized else None
        return Decimal(str(value))
