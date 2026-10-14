"""Add persistent PLC node settings.

Revision ID: b8dad9f2556c
Revises: 13bbe5395414
Create Date: 2026-10-12 12:37:03.769895
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "b8dad9f2556c"
down_revision: Union[str, Sequence[str], None] = "13bbe5395414"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("opcua_node_production_order", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("opcua_node_delivery_order", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("polling_interval_ms", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("settings")
