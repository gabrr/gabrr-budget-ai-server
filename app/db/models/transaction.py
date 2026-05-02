from __future__ import annotations

from datetime import date as DateValue

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.categories import ExpenseCategory


class Transaction(BaseModel):
    """Single transaction contract used by the current API prototype.

    This is intentionally an interface/schema object, not a database table
    definition. Database table definitions should live in the DB model layer.
    """

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    date: DateValue | None = None
    description: str | None = Field(default=None, min_length=1)
    amount: float | None = None
    currency: str | None = None
    merchant: str | None = None
    category: ExpenseCategory | None = None
    payment_method: str | None = Field(
        default=None,
        description="debit, credit, pix, or unknown",
    )
    installments: int | None = None
    installments_current: int | None = None
    card_name: str | None = None
    comment: str | None = None
    tags: list[str] | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def _amount_as_float(cls, value: object) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
            return float(normalized) if normalized else None
        return float(value)
