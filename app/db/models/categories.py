"""Category enum and REST models for the API."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from app.db.models.base import TimestampModel


class ExpenseCategory(str, Enum):
    """Fixed vocabulary for `category` on transactions (JSON uses the value strings)."""

    FOOD = "food"
    TRANSPORTATION = "transportation"
    HEALTH = "health"
    LEISURE = "leisure"
    NEEDS = "needs"
    FUN = "fun"
    DONATIONS = "donations"
    CLOTHING = "clothing"
    RENTING = "renting"
    HOME = "home"
    COMPANY = "company"
    OTHERS = "others"

class Category(TimestampModel):
    id: str | None = None
    user_id: str | None = None
    key: ExpenseCategory
    name: str = Field(min_length=1)
    is_system: bool = False


