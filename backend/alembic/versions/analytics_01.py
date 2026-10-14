"""Persist observed production and delivery run analytics."""

from alembic import op
import sqlalchemy as sa


revision = "analytics_01"
down_revision = "13bbe5395414"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "productionrun" not in inspector.get_table_names():
        op.create_table(
            "productionrun",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("order_type", sa.String(length=16), nullable=False),
            sa.Column("order_id", sa.String(length=128), nullable=False),
            sa.Column("plc_order_number", sa.Integer(), nullable=True),
            sa.Column("planned_quantity", sa.Integer(), nullable=True),
            sa.Column("processed_quantity", sa.Integer(), nullable=True),
            sa.Column("good_quantity", sa.Integer(), nullable=True),
            sa.Column("defective_quantity", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("ended_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("last_observed_at", sa.DateTime(), nullable=True),
            sa.Column("last_error_type", sa.String(length=128), nullable=True),
        )
        inspector = sa.inspect(op.get_bind())
    if "ix_productionrun_order_type" not in {
        index["name"] for index in inspector.get_indexes("productionrun")
    }:
        op.create_index("ix_productionrun_order_type", "productionrun", ["order_type"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT 1 FROM productionrun LIMIT 1")).first():
        # Run history is operational data; keep it available across a code rollback.
        return
    op.drop_index("ix_productionrun_order_type", table_name="productionrun")
    op.drop_table("productionrun")
