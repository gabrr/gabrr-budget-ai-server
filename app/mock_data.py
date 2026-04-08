from __future__ import annotations

from datetime import date
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException, status

from app.schemas import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    ExpenseCategory,
    Transaction,
    TransactionBulkCreate,
    TransactionCreate,
    TransactionUpdate,
)

DEFAULT_CATEGORIES: list[tuple[ExpenseCategory, str]] = [
    ("food", "Food"),
    ("transportation", "Transport"),
    ("health", "Health"),
    ("leisure", "Leisure"),
    ("needs", "Needs"),
    ("fun", "Fun"),
    ("donations", "Donations"),
    ("clothing", "Clothing"),
    ("renting", "Renting"),
    ("home", "Home"),
    ("company", "Company"),
    ("others", "Others"),
]

DEFAULT_TRANSACTIONS: list[dict] = [
    {"id": "1", "description": "Grocery shopping", "amount": 142.80, "date": date(2026, 4, 20), "category": "food", "merchant": "Whole Foods"},
    {"id": "2", "description": "Uber ride", "amount": 26.10, "date": date(2026, 4, 19), "category": "transportation", "merchant": "Uber"},
    {"id": "3", "description": "Pharmacy", "amount": 58.20, "date": date(2026, 4, 18), "category": "health", "merchant": "CVS"},
    {"id": "4", "description": "Movie tickets", "amount": 34.50, "date": date(2026, 4, 17), "category": "leisure", "merchant": "AMC Theaters"},
    {"id": "5", "description": "Coffee shop", "amount": 9.25, "date": date(2026, 4, 20), "category": "food", "merchant": "Starbucks"},
    {"id": "6", "description": "Gas station", "amount": 72.00, "date": date(2026, 4, 19), "category": "transportation", "merchant": "Shell"},
    {"id": "7", "description": "Restaurant dinner", "amount": 96.40, "date": date(2026, 4, 18), "category": "food", "merchant": "Italian Bistro"},
    {"id": "8", "description": "Online purchase", "amount": 184.90, "date": date(2026, 4, 21), "category": "others", "merchant": "Amazon"},
    {"id": "9", "description": "Monthly subscription", "amount": 19.99, "date": date(2026, 4, 20), "category": "others", "merchant": "Unknown Service"},
    {"id": "10", "description": "Hardware store", "amount": 83.20, "date": date(2026, 4, 19), "category": "others", "merchant": "Home Depot"},
    {"id": "13", "description": "Weekend getaway", "amount": 120.00, "date": date(2026, 3, 28), "category": "leisure", "merchant": "Airbnb"},
    {"id": "14", "description": "Fuel stop", "amount": 48.00, "date": date(2026, 3, 15), "category": "transportation", "merchant": "Shell"},
    {"id": "15", "description": "Spring furniture order", "amount": 420.00, "date": date(2026, 5, 3), "category": "others", "merchant": "IKEA"},
    {"id": "16", "description": "Last year groceries", "amount": 94.00, "date": date(2025, 4, 12), "category": "food", "merchant": "Trader Joes"},
]


class MockBudgetStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._categories = {
                key: Category(id=key, key=key, name=name)
                for key, name in DEFAULT_CATEGORIES
            }
            self._transactions = {
                row["id"]: Transaction(**row)
                for row in DEFAULT_TRANSACTIONS
            }

    def list_categories(self) -> list[Category]:
        ordered_keys = {key: index for index, (key, _) in enumerate(DEFAULT_CATEGORIES)}
        categories = list(self._categories.values())
        categories.sort(key=lambda category: (ordered_keys.get(category.key, len(ordered_keys)), category.name))
        return [category.model_copy(deep=True) for category in categories]

    def get_category(self, category_id: str) -> Category:
        category = self._categories.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category.model_copy(deep=True)

    def create_category(self, payload: CategoryCreate) -> Category:
        category_id = payload.key
        with self._lock:
            if category_id in self._categories:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
            category = Category(id=category_id, key=payload.key, name=payload.name)
            self._categories[category.id] = category
        return category.model_copy(deep=True)

    def update_category(self, category_id: str, payload: CategoryUpdate) -> Category:
        with self._lock:
            category = self._categories.get(category_id)
            if not category:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
            updated = category.model_copy(update=payload.model_dump(exclude_none=True))
            self._categories[category_id] = updated
        return updated.model_copy(deep=True)

    def delete_category(self, category_id: str) -> dict[str, str]:
        with self._lock:
            if category_id not in self._categories:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
            if category_id == "others":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the fallback category",
                )
            del self._categories[category_id]
        return {"status": "deleted", "id": category_id}

    def list_transactions(
        self,
        *,
        category: ExpenseCategory | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        items = list(self._transactions.values())
        items.sort(key=lambda row: (row.date, row.id), reverse=True)

        if category is not None:
            items = [item for item in items if item.category == category]
        if date_from is not None:
            items = [item for item in items if item.date >= date_from]
        if date_to is not None:
            items = [item for item in items if item.date <= date_to]

        total = len(items)
        paginated = items[offset : offset + limit]
        return [item.model_copy(deep=True) for item in paginated], total

    def get_transaction(self, transaction_id: str) -> Transaction:
        transaction = self._transactions.get(transaction_id)
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
        return transaction.model_copy(deep=True)

    def create_transaction(self, payload: TransactionCreate) -> Transaction:
        transaction_id = payload.id or f"tx_{uuid4().hex[:10]}"
        with self._lock:
            if transaction_id in self._transactions:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Transaction already exists")
            transaction = Transaction(id=transaction_id, **payload.model_dump(exclude={"id"}))
            self._transactions[transaction.id] = transaction
        return transaction.model_copy(deep=True)

    def bulk_create_transactions(self, payload: TransactionBulkCreate) -> list[Transaction]:
        created: list[Transaction] = []
        for transaction in payload.transactions:
            created.append(self.create_transaction(transaction))
        return created

    def update_transaction(self, transaction_id: str, payload: TransactionUpdate) -> Transaction:
        with self._lock:
            current = self._transactions.get(transaction_id)
            if not current:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
            updated = current.model_copy(update=payload.model_dump(exclude_none=True))
            self._transactions[transaction_id] = updated
        return updated.model_copy(deep=True)

    def delete_transaction(self, transaction_id: str) -> dict[str, str]:
        with self._lock:
            if transaction_id not in self._transactions:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
            del self._transactions[transaction_id]
        return {"status": "deleted", "id": transaction_id}


store = MockBudgetStore()
