"""Category enum and REST models for the API."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.db.models.base import DbModel, TimestampModel


class ExpenseCategory(StrEnum):
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


class CategoryBase(DbModel):
    key: ExpenseCategory
    name: str = Field(min_length=1)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(DbModel):
    name: str | None = Field(default=None, min_length=1)


class Category(CategoryBase, TimestampModel):
    id: str | None = None
    user_id: str | None = None
    is_system: bool = False
