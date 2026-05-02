from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_id


class DraftTransactionSchema(TimestampMixin, Base):
    __tablename__ = "draft_transactions"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: new_id("dtx"),
    )
    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    source_row_index: Mapped[int | None]
    account_id: Mapped[str | None] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"))
    posted_at: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(500))
    merchant_name: Mapped[str | None] = mapped_column(String(255))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    payment_method: Mapped[str | None] = mapped_column(String(40))
    installments: Mapped[int | None]
    installments_current: Mapped[int | None]
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    needs_review: Mapped[bool] = mapped_column(default=True, nullable=False)
    review_reason: Mapped[str | None] = mapped_column(String(500))
    duplicate_of_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id"),
    )
    status: Mapped[str] = mapped_column(String(40), default="draft", nullable=False)
    raw_payload_json: Mapped[dict | None] = mapped_column(JSON)
    committed_transaction_id: Mapped[str | None] = mapped_column(
        ForeignKey("transactions.id"),
    )

    account = relationship("AccountSchema", back_populates="draft_transactions")
    category = relationship("CategorySchema", back_populates="draft_transactions")
    committed_transaction = relationship(
        "TransactionSchema",
        foreign_keys=[committed_transaction_id],
        post_update=True,
    )
    duplicate_of_transaction = relationship(
        "TransactionSchema",
        foreign_keys=[duplicate_of_transaction_id],
    )
    import_record = relationship("ImportSchema", back_populates="draft_transactions")
