from __future__ import annotations

from datetime import date as DateValue
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CategoryKey = Literal[
    "food",
    "transportation",
    "health",
    "leisure",
    "needs",
    "fun",
    "donations",
    "credit",
    "clothing",
    "renting",
    "home",
    "company",
    "others",
]


class CategoryBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: CategoryKey
    name: str = Field(min_length=1)


class Category(CategoryBase):
    id: str


class CategoryCreate(CategoryBase):
    id: str | None = None


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1)


class TransactionBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    amount: float
    date: DateValue
    category: CategoryKey
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
    category: CategoryKey | None = None
    merchant: str | None = None


class TransactionBulkCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transactions: list[TransactionCreate]


class TransactionListResponse(BaseModel):
    items: list[Transaction]
    total: int
    limit: int
    offset: int
