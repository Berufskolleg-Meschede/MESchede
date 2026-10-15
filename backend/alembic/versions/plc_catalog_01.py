"""Spiegelt den gelesenen SPS-Produktkatalog ohne Änderungen am Artikel-/Auftragsbestand."""

from alembic import op
import sqlalchemy as sa


revision = "plc_catalog_01"
down_revision = "1172056ef1d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ergänzt ausschließlich zwei neue Katalogtabellen."""
    op.create_table(
        "plc_catalog_product",
        sa.Column("product_id", sa.Integer(), primary_key=True),
        sa.Column("product_text", sa.String(30), nullable=False),
        sa.Column("source_index", sa.Integer()),
        sa.Column("specification", sa.JSON(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "plc_catalog_state",
        sa.Column("order_type", sa.String(), primary_key=True),
        sa.Column("capacity", sa.Integer()),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error", sa.String()),
    )


def downgrade() -> None:
    """Entfernt nur den Katalogspiegel, niemals Aufträge oder Artikel."""
    op.drop_table("plc_catalog_state")
    op.drop_table("plc_catalog_product")
