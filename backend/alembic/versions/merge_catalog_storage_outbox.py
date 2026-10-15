"""Führt Produktkatalog und RabbitMQ-Lageroutbox zu einem Migrationsziel zusammen."""


revision = "merge_catalog_storage_outbox"
down_revision = ("plc_catalog_01", "storage_outbox_01")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Beide Vorgängermigrationen enthalten bereits die benötigten Schemaänderungen."""
    pass


def downgrade() -> None:
    """Trennt nur die Migrationszweige, ohne Tabellen oder Daten zu verändern."""
    pass
