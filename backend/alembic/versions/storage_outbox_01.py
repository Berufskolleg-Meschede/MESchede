"""Persist confirmed production and delivery stock deltas for RabbitMQ."""

from alembic import op
import sqlalchemy as sa


revision = "storage_outbox_01"
down_revision = "merge_settings_storage_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storage_outbox_event",
        sa.Column("event_id", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("quantity_delta IN (-1, 1)", name="ck_storage_outbox_unit_delta"),
    )
    op.create_index(
        "ix_storage_outbox_pending",
        "storage_outbox_event",
        ["published_at", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_storage_outbox_pending", table_name="storage_outbox_event")
    op.drop_table("storage_outbox_event")
