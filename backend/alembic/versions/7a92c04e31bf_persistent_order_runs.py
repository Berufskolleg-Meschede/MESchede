"""Persistente Auftragsläufe, FIFO-Koordination und manuelle Ergebnisprüfung."""

from alembic import op
import sqlalchemy as sa


revision = "7a92c04e31bf"
down_revision = "13bbe5395414"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ergänzt die Auftragsdomäne ohne bestehende Maschinen-/Benutzerdaten zu verändern."""
    op.create_table(
        "mes_order",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("order_type", sa.String(), nullable=False),
        sa.Column("order_id", sa.String(), nullable=False),
        sa.Column("plc_order_number", sa.Integer(), nullable=False),
        sa.Column("accepted_sequence", sa.Integer(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("order_type", "order_id"),
        sa.UniqueConstraint("order_type", "plc_order_number"),
        sa.UniqueConstraint("accepted_sequence"),
    )
    op.create_index("ix_mes_order_order_type", "mes_order", ["order_type"])
    op.create_index("ix_mes_order_accepted_sequence", "mes_order", ["accepted_sequence"])
    op.create_table(
        "order_run",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("order_ref", sa.String(), sa.ForeignKey("mes_order.id"), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("review_reason", sa.String()),
        sa.Column("last_observed_status", sa.Integer()),
        sa.Column("result_observed", sa.Boolean(), nullable=False),
        sa.Column("manual_good_quantity", sa.Integer()),
        sa.Column("manual_error_quantity", sa.Integer()),
        sa.Column("has_manual_review", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("phase_changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("order_ref"),
    )
    op.create_index("ix_order_run_order_ref", "order_run", ["order_ref"])
    op.create_table(
        "product_unit",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("order_run.id"), nullable=False),
        sa.Column("queue_index", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("product_text", sa.String(), nullable=False),
        sa.Column("serial_number", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("result", sa.String()),
        sa.Column("raw_status", sa.Integer()),
        sa.Column("error_code", sa.Integer()),
        sa.UniqueConstraint("run_id", "queue_index"),
        sa.CheckConstraint("result IS NULL OR result IN ('good', 'failed')"),
    )
    op.create_index("ix_product_unit_run_id", "product_unit", ["run_id"])
    op.create_table(
        "run_review",
        sa.Column("request_id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("order_run.id"), nullable=False),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("good_quantity", sa.Integer()),
        sa.Column("error_quantity", sa.Integer()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
    )
    op.create_index("ix_run_review_run_id", "run_review", ["run_id"])
    op.create_table(
        "dispatch_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("accepted_sequence", sa.Integer(), nullable=False),
        sa.Column("active_run_id", sa.String(), sa.ForeignKey("order_run.id")),
        sa.Column("blocked_reason", sa.String()),
    )
    op.create_table(
        "plc_source_state",
        sa.Column("order_type", sa.String(), primary_key=True),
        sa.Column("connection_status", sa.String(), nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.String()),
    )
    op.execute(sa.text("INSERT INTO dispatch_state (id, accepted_sequence) VALUES (1, 0)"))
    op.execute(sa.text(
        "INSERT INTO plc_source_state (order_type, connection_status) "
        "VALUES ('production', 'unknown'), ('delivery', 'unknown')"
    ))


def downgrade() -> None:
    """Entfernt ausschließlich die durch diese Revision ergänzte Auftragsdomäne."""
    for table in ("plc_source_state", "dispatch_state", "run_review", "product_unit", "order_run", "mes_order"):
        op.drop_table(table)
