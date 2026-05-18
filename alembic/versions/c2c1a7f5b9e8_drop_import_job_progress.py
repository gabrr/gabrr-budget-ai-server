"""drop import job progress

Revision ID: c2c1a7f5b9e8
Revises: 8b6a2f4c9d10
Create Date: 2026-05-18 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2c1a7f5b9e8"
down_revision: Union[str, Sequence[str], None] = "8b6a2f4c9d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("import_jobs") as batch_op:
        batch_op.drop_column("progress")


def downgrade() -> None:
    with op.batch_alter_table("import_jobs") as batch_op:
        batch_op.add_column(sa.Column("progress", sa.Integer(), nullable=False, server_default="5"))

