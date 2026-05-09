import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    ExpenseCategory,
    Transaction,
)
from app.db.repositories.transactions import (
    TransactionRepository,
    transaction_schema_to_model,
)
from app.db.session import get_session

router = APIRouter()
logger = logging.getLogger(__name__)

_tx_repo = TransactionRepository()


class TransactionsBulkIn(BaseModel):
    transactions: list[Transaction] = Field(min_length=1)


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
    session: Session = Depends(get_session),
    category: ExpenseCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, object]:
    rows, total = _tx_repo.list_filtered(
        session,
        user_id=settings.default_user_id,
        category=category,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    items = [transaction_schema_to_model(r) for r in rows]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.post("/transactions", response_model=Transaction, status_code=201)
async def create_transaction(
    payload: Transaction,
    session: Session = Depends(get_session),
) -> Transaction:
    try:
        row = _tx_repo.create(
            session,
            payload,
            default_user_id=settings.default_user_id,
            default_account_id=settings.default_account_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return transaction_schema_to_model(row)


@router.post("/transactions/bulk", response_model=list[Transaction], status_code=201)
async def bulk_create_transactions(
    payload: TransactionsBulkIn,
    session: Session = Depends(get_session),
) -> list[Transaction]:
    try:
        rows = _tx_repo.create_many(
            session,
            payload.transactions,
            default_user_id=settings.default_user_id,
            default_account_id=settings.default_account_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return [transaction_schema_to_model(r) for r in rows]


@router.get("/transactions/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: str,
    session: Session = Depends(get_session),
) -> Transaction:
    row = _tx_repo.get_by_id(
        session,
        user_id=settings.default_user_id,
        transaction_id=transaction_id,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction_schema_to_model(row)


@router.patch("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: str,
    payload: Transaction,
    session: Session = Depends(get_session),
) -> Transaction:
    row = _tx_repo.update(
        session,
        user_id=settings.default_user_id,
        transaction_id=transaction_id,
        payload=payload,
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction_schema_to_model(row)


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    deleted = _tx_repo.delete_by_id(
        session,
        user_id=settings.default_user_id,
        transaction_id=transaction_id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "deleted", "id": transaction_id}
