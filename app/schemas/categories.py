"""Category enum and REST models for the API."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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


class CategoryBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: ExpenseCategory
    name: str = Field(min_length=1)


class Category(CategoryBase):
    id: str


class CategoryCreate(CategoryBase):
    id: str | None = None


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1)
