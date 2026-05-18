from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, new_id


class ImportJobSchema(TimestampMixin, Base):
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: new_id("job"),
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(120))
    source_type: Mapped[str] = mapped_column(String(40), default="pdf", nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    agent_input_payload_json: Mapped[dict | None] = mapped_column(JSON)
    agent_output_payload_json: Mapped[dict | None] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_by: Mapped[str | None] = mapped_column(String(120))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(1000))

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_import_jobs_user_idempotency_key"),
    )
