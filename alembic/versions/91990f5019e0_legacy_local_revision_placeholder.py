"""legacy local revision placeholder

Revision ID: 91990f5019e0
Revises: 574f0c9b4e44
Create Date: 2026-05-17 00:00:00.000000

This checkout was used with a database already stamped at this revision,
but the migration file was missing from the repository. Keep this no-op
placeholder so Alembic can continue the migration graph safely.
"""

from typing import Sequence, Union

revision: str = "91990f5019e0"
down_revision: Union[str, Sequence[str], None] = "574f0c9b4e44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
