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
from app.mock_data import store

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/categories", response_model=list[Category])
async def list_categories() -> list[Category]:
    return store.list_categories()


@router.post("/categories", response_model=Category, status_code=201)
async def create_category(payload: CategoryCreate) -> Category:
    return store.create_category(payload)


@router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: str) -> Category:
    return store.get_category(category_id)


@router.patch("/categories/{category_id}", response_model=Category)
async def update_category(category_id: str, payload: CategoryUpdate) -> Category:
    return store.update_category(category_id, payload)


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str) -> dict[str, str]:
    return store.delete_category(category_id)


@router.get("/transactions")
async def list_transactions(
    category: ExpenseCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    items, total = store.list_transactions(
        category=category,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/transactions", response_model=Transaction, status_code=201)
async def create_transaction(payload: Transaction) -> Transaction:
    return store.create_transaction(payload)


@router.post("/transactions/bulk", response_model=list[Transaction], status_code=201)
async def bulk_create_transactions(payload: dict[str, list[Transaction]]) -> list[Transaction]:
    return store.bulk_create_transactions(payload)


@router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str) -> Transaction:
    return store.get_transaction(transaction_id)


@router.patch("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, payload: Transaction) -> Transaction:
    return store.update_transaction(transaction_id, payload)


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str) -> dict[str, str]:
    return store.delete_transaction(transaction_id)
