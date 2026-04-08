from __future__ import annotations

from datetime import date as DateValue

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.categories import ExpenseCategory


class TransactionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    amount: float
    date: DateValue
    category: ExpenseCategory
    merchant: str | None = None


class Transaction(TransactionBase):
    id: str


class TransactionCreate(TransactionBase):
    id: str | None = None


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(default=None, min_length=1)
    amount: float | None = None
    date: DateValue | None = None
    category: ExpenseCategory | None = None
    merchant: str | None = None


class TransactionBulkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transactions: list[TransactionCreate]


class TransactionListResponse(BaseModel):
    items: list[Transaction]
    total: int
    limit: int
    offset: int


class TransactionLine(BaseModel):
    """One parsed line from a bank or card file (ingestion / LLM output)."""

    date: str | None = None
    description: str | None = None
    amount: str | None = None
    currency: str | None = None
    payment_method: str | None = Field(
        default=None,
        description="debit, credit, pix, or unknown",
    )
    installments: int | None = None
    installments_current: int | None = None
    card_name: str | None = None
    category: ExpenseCategory | None = Field(
        default=None,
        description=(
            "One of: food, transportation, health, leisure, needs, fun, donations, "
            "clothing, renting, home, company, others; null if unclear."
        ),
    )
    comment: str | None = None
    tags: list[str] | None = None

    @field_validator("amount", mode="before")
    @classmethod
    def _amount_as_string(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return value
        return str(value)


class TransactionBatch(BaseModel):
    """Normalized import payload: a list of parsed lines (e.g. from the normalizer)."""

    transactions: list[TransactionLine] = Field(default_factory=list)
