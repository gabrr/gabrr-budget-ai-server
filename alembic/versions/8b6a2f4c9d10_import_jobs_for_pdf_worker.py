"""import jobs for pdf worker

Revision ID: 8b6a2f4c9d10
Revises: 91990f5019e0
Create Date: 2026-05-17 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8b6a2f4c9d10"
down_revision: Union[str, Sequence[str], None] = "91990f5019e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("import_jobs") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("progress", sa.Integer(), nullable=False, server_default="5"))
        batch_op.add_column(sa.Column("current_step", sa.String(length=120), nullable=True))
        batch_op.add_column(
            sa.Column("source_type", sa.String(length=40), nullable=False, server_default="pdf")
        )
        batch_op.add_column(sa.Column("original_filename", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("content_type", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("size_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("storage_path", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("file_hash", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("agent_input_payload_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("agent_output_payload_json", sa.JSON(), nullable=True))
        batch_op.create_foreign_key("fk_import_jobs_user_id_users", "users", ["user_id"], ["id"])
        batch_op.create_unique_constraint(
            "uq_import_jobs_user_idempotency_key",
            ["user_id", "idempotency_key"],
        )
        batch_op.drop_column("import_id")


def downgrade() -> None:
    with op.batch_alter_table("import_jobs") as batch_op:
        batch_op.add_column(sa.Column("import_id", sa.String(length=32), nullable=True))
        batch_op.drop_constraint("uq_import_jobs_user_idempotency_key", type_="unique")
        batch_op.drop_constraint("fk_import_jobs_user_id_users", type_="foreignkey")
        batch_op.drop_column("agent_output_payload_json")
        batch_op.drop_column("agent_input_payload_json")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("file_hash")
        batch_op.drop_column("storage_path")
        batch_op.drop_column("size_bytes")
        batch_op.drop_column("content_type")
        batch_op.drop_column("original_filename")
        batch_op.drop_column("source_type")
        batch_op.drop_column("current_step")
        batch_op.drop_column("progress")
        batch_op.drop_column("user_id")
