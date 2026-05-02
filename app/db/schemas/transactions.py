from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_id


class TransactionSchema(TimestampMixin, Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: new_id("tx"),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    source_import_id: Mapped[str | None] = mapped_column(ForeignKey("imports.id"))
    source_draft_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("draft_transactions.id"),
    )
    posted_at: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    merchant_name: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(40))
    installments: Mapped[int | None]
    installments_current: Mapped[int | None]
    reverted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    account = relationship("AccountSchema", back_populates="transactions")
    category = relationship("CategorySchema", back_populates="transactions")
    source_draft_transaction = relationship(
        "DraftTransactionSchema",
        foreign_keys=[source_draft_transaction_id],
    )
    source_import = relationship("ImportSchema", back_populates="transactions")
    user = relationship("UserSchema", back_populates="transactions")
