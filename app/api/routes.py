import logging
from datetime import date

from fastapi import APIRouter, Query

from app.db.models import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    ExpenseCategory,
    Transaction,
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/categories", response_model=list[Category])
async def list_categories() -> list[Category]:
    return []


@router.post("/categories", response_model=Category, status_code=201)
async def create_category(payload: CategoryCreate) -> Category:
    return []


@router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str) -> Category:
    return []


@router.patch("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, payload: CategoryUpdate) -> Category:
    return []


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str) -> dict[str, str]:
    return []


@router.get("/transactions")
async def list_transactions(
    category: ExpenseCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    items, total = [], 0
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/transactions", response_model=Transaction, status_code=201)
async def create_transaction(payload: Transaction) -> Transaction:
    return []


@router.post("/transactions/bulk", response_model=list[Transaction], status_code=201)
async def bulk_create_transactions(payload: dict[str, list[Transaction]]) -> list[Transaction]:
    return []


@router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str) -> Transaction:
    return []


@router.patch("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, payload: Transaction) -> Transaction:
    return []


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str) -> dict[str, str]:
    return []
