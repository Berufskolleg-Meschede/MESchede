"""Assume successful units on a confirmed order completion when no result is mapped.

Revision ID: c1a9f8274d65
Revises: 7a92c04e31bf
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a9f8274d65"
down_revision: Union[str, Sequence[str], None] = "7a92c04e31bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_run",
        sa.Column("completion_assumed", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("order_run", "completion_assumed")
