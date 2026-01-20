"""Pydantic schemas for agent inputs and outputs."""

from typing import Literal

from pydantic import BaseModel


class Transaction(BaseModel):
    """Normalized transaction record.

    This is the strict output schema for parsed transactions.
    """

    date: str | None
    """Date in YYYY-MM-DD format, or null if cannot parse confidently."""

    description: str
    """Transaction description, trimmed."""

    amount: float
    """Numeric amount (positive or negative)."""

    currency: str | None
    """Currency code if detected, else null."""

    merchant_raw: str | None
    """Best effort merchant extraction, or description if unknown."""

    source: Literal["csv", "pdf"]
    """Source file type."""


class ParseError(BaseModel):
    """Error response for parsing failures."""

    error: Literal["PARSE_FAILED"]
    """Error code."""

    detail: str
    """Short description of what went wrong."""
