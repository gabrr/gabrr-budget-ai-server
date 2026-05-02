from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, new_id


class AgentRunSchema(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: new_id("arun"),
    )
    import_id: Mapped[str] = mapped_column(ForeignKey("imports.id"), nullable=False)
    uploaded_file_id: Mapped[str] = mapped_column(
        ForeignKey("uploaded_files.id"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="running", nullable=False)
    input_payload_json: Mapped[dict | None] = mapped_column(JSON)
    output_payload_json: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(String(1000))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    import_record = relationship("ImportSchema", back_populates="agent_runs")
    uploaded_file = relationship("UploadedFileSchema", back_populates="agent_runs")
