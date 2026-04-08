import logging
import os
import tempfile
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Query, UploadFile
from docling.document_converter import DocumentConverter

from app.mock_data import store
from app.schemas import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    ExpenseCategory,
    Transaction,
    TransactionBulkCreate,
    TransactionCreate,
    TransactionListResponse,
    TransactionUpdate,
)
from app.utils.files import writeToExternalMd

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


@router.get("/transactions", response_model=TransactionListResponse)
async def list_transactions(
    category: ExpenseCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TransactionListResponse:
    items, total = store.list_transactions(
        category=category,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return TransactionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/transactions", response_model=Transaction, status_code=201)
async def create_transaction(payload: TransactionCreate) -> Transaction:
    return store.create_transaction(payload)


@router.post("/transactions/bulk", response_model=list[Transaction], status_code=201)
async def bulk_create_transactions(payload: TransactionBulkCreate) -> list[Transaction]:
    return store.bulk_create_transactions(payload)


@router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(transaction_id: str) -> Transaction:
    return store.get_transaction(transaction_id)


@router.patch("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(transaction_id: str, payload: TransactionUpdate) -> Transaction:
    return store.update_transaction(transaction_id, payload)


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str) -> dict[str, str]:
    return store.delete_transaction(transaction_id)


