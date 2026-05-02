from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_id


class ImportJobSchema(TimestampMixin, Base):
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: new_id("job"),
    )
    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_by: Mapped[str | None] = mapped_column(String(120))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(1000))

    import_record = relationship("ImportSchema", back_populates="jobs")
