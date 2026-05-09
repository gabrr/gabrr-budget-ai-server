from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.db.models.categories import ExpenseCategory
from app.db.models.transaction import Transaction
from app.db.schemas.categories import CategorySchema
from app.db.schemas.transactions import TransactionSchema


def transaction_schema_to_model(
    row: TransactionSchema,
    *,
    category_key: str | None = None,
) -> Transaction:
    """Map ORM row to API Transaction; extra Pydantic-only fields stay unset."""
    cat = category_key
    if cat is None and row.category_id and row.category is not None:
        cat = row.category.key

    category_enum = ExpenseCategory(cat) if cat else None

    return Transaction(
        id=row.id,
        user_id=row.user_id,
        account_id=row.account_id,
        category_id=row.category_id,
        category=category_enum,
        source_import_id=row.source_import_id,
        source_draft_transaction_id=row.source_draft_transaction_id,
        posted_at=row.posted_at,
        date=row.posted_at,
        description=row.description,
        merchant_name=row.merchant_name,
        amount=row.amount,
        currency=row.currency,
        payment_method=row.payment_method,
        installments=row.installments,
        installments_current=row.installments_current,
        reverted_at=row.reverted_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class TransactionRepository:
    """Stateless persistence for TransactionSchema."""

    def list_filtered(
        self,
        session: Session,
        *,
        user_id: str,
        category: ExpenseCategory | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TransactionSchema], int]:
        base = select(TransactionSchema).where(TransactionSchema.user_id == user_id)
        count_base = select(func.count()).select_from(TransactionSchema).where(
            TransactionSchema.user_id == user_id,
        )

        if category is not None:
            base = (
                select(TransactionSchema)
                .join(
                    CategorySchema,
                    TransactionSchema.category_id == CategorySchema.id,
                )
                .where(
                    TransactionSchema.user_id == user_id,
                    CategorySchema.key == category.value,
                )
                .options(contains_eager(TransactionSchema.category))
            )
            count_base = (
                select(func.count())
                .select_from(TransactionSchema)
                .join(
                    CategorySchema,
                    TransactionSchema.category_id == CategorySchema.id,
                )
                .where(
                    TransactionSchema.user_id == user_id,
                    CategorySchema.key == category.value,
                )
            )

        if date_from is not None:
            base = base.where(TransactionSchema.posted_at >= date_from)
            count_base = count_base.where(TransactionSchema.posted_at >= date_from)
        if date_to is not None:
            base = base.where(TransactionSchema.posted_at <= date_to)
            count_base = count_base.where(TransactionSchema.posted_at <= date_to)

        total = int(session.execute(count_base).scalar_one())

        if category is not None:
            stmt = (
                base.order_by(TransactionSchema.posted_at.desc())
                .limit(limit)
                .offset(offset)
            )
        else:
            stmt = (
                base.options(joinedload(TransactionSchema.category))
                .order_by(TransactionSchema.posted_at.desc())
                .limit(limit)
                .offset(offset)
            )
        rows = list(session.scalars(stmt).unique().all())
        return rows, total

    def get_by_id(
        self,
        session: Session,
        *,
        user_id: str,
        transaction_id: str,
    ) -> TransactionSchema | None:
        stmt = (
            select(TransactionSchema)
            .where(
                TransactionSchema.id == transaction_id,
                TransactionSchema.user_id == user_id,
            )
            .options(joinedload(TransactionSchema.category))
        )
        return session.scalars(stmt).first()

    def create(
        self,
        session: Session,
        payload: Transaction,
        *,
        default_user_id: str,
        default_account_id: str,
    ) -> TransactionSchema:
        posted = payload.posted_at or payload.date
        if posted is None:
            raise ValueError("posted_at or date is required")
        if payload.description is None or not str(payload.description).strip():
            raise ValueError("description is required")
        if payload.amount is None:
            raise ValueError("amount is required")

        user_id = payload.user_id or default_user_id
        account_id = payload.account_id or default_account_id

        row = TransactionSchema(
            user_id=user_id,
            account_id=account_id,
            category_id=payload.category_id,
            source_import_id=payload.source_import_id,
            source_draft_transaction_id=payload.source_draft_transaction_id,
            posted_at=posted,
            description=payload.description.strip(),
            merchant_name=payload.merchant_name,
            amount=Decimal(str(payload.amount)),
            currency=(payload.currency or "BRL").upper()[:3],
            payment_method=payload.payment_method,
            installments=payload.installments,
            installments_current=payload.installments_current,
            reverted_at=payload.reverted_at,
        )
        session.add(row)
        session.flush()
        session.refresh(row, ["category"])
        return row

    def create_many(
        self,
        session: Session,
        items: list[Transaction],
        *,
        default_user_id: str,
        default_account_id: str,
    ) -> list[TransactionSchema]:
        out: list[TransactionSchema] = []
        for payload in items:
            out.append(
                self.create(
                    session,
                    payload,
                    default_user_id=default_user_id,
                    default_account_id=default_account_id,
                )
            )
        return out

    def update(
        self,
        session: Session,
        *,
        user_id: str,
        transaction_id: str,
        payload: Transaction,
    ) -> TransactionSchema | None:
        row = self.get_by_id(session, user_id=user_id, transaction_id=transaction_id)
        if row is None:
            return None

        data = payload.model_dump(exclude_unset=True, exclude={"id", "category"})
        if "date" in data and "posted_at" not in data:
            data["posted_at"] = data.pop("date")
        elif "date" in data and "posted_at" in data:
            data.pop("date", None)

        field_map = {
            "user_id": "user_id",
            "account_id": "account_id",
            "category_id": "category_id",
            "source_import_id": "source_import_id",
            "source_draft_transaction_id": "source_draft_transaction_id",
            "posted_at": "posted_at",
            "description": "description",
            "merchant_name": "merchant_name",
            "payment_method": "payment_method",
            "installments": "installments",
            "installments_current": "installments_current",
            "reverted_at": "reverted_at",
        }
        for pydantic_key, orm_key in field_map.items():
            if pydantic_key in data:
                setattr(row, orm_key, data[pydantic_key])
        if "amount" in data and data["amount"] is not None:
            row.amount = Decimal(str(data["amount"]))
        if "currency" in data and data["currency"] is not None:
            row.currency = str(data["currency"]).upper()[:3]
        if "description" in data and data["description"] is not None:
            row.description = str(data["description"]).strip()

        session.flush()
        session.refresh(row, ["category"])
        return row

    def delete_by_id(
        self,
        session: Session,
        *,
        user_id: str,
        transaction_id: str,
    ) -> bool:
        row = self.get_by_id(session, user_id=user_id, transaction_id=transaction_id)
        if row is None:
            return False
        session.delete(row)
        return True
