"""Merge heads: settings table, RabbitMQ inventory, and run analytics.

Revision ID: merge_settings_storage_analytics
Revises: b8dad9f2556c, inventory_rabbitmq_01, analytics_01
Create Date: 2026-10-14 00:00:00.000000

"""

revision = "merge_settings_storage_analytics"
down_revision = ("b8dad9f2556c", "inventory_rabbitmq_01", "analytics_01")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
