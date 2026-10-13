"""Persist RabbitMQ inventory state and deduplicate delivered events."""

from alembic import op
import sqlalchemy as sa


revision = "inventory_rabbitmq_01"
down_revision = "13bbe5395414"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "article" not in tables:
        op.create_table(
            "article",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
        )

    if "storage" not in tables:
        op.create_table(
            "storage",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=True),
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["article_id"], ["article.id"]),
            sa.UniqueConstraint("article_id", name="uq_storage_article_id"),
        )
    else:
        columns = {column["name"] for column in inspector.get_columns("storage")}
        if "updated_at" not in columns:
            op.add_column("storage", sa.Column("updated_at", sa.DateTime(), nullable=True))
        quantity_column = next(
            column for column in inspector.get_columns("storage") if column["name"] == "quantity"
        )
        if not quantity_column["nullable"]:
            op.alter_column("storage", "quantity", existing_type=sa.Integer(), nullable=True)

        indexes = {index["name"] for index in inspector.get_indexes("storage")}
        constraints = {
            constraint["name"] for constraint in inspector.get_unique_constraints("storage")
        }
        if "uq_storage_article_id" not in indexes and "uq_storage_article_id" not in constraints:
            duplicates = bind.execute(
                sa.text(
                    "SELECT article_id FROM storage GROUP BY article_id "
                    "HAVING COUNT(*) > 1 LIMIT 1"
                )
            ).first()
            if duplicates:
                raise RuntimeError(
                    "Die storage-Tabelle enthält mehrere Zeilen pro Artikel; "
                    "vor der Lagerintegration müssen Duplikate manuell geklärt werden."
                )
            op.create_unique_constraint("uq_storage_article_id", "storage", ["article_id"])

    if "storageevent" not in tables:
        op.create_table(
            "storageevent",
            sa.Column("event_id", sa.String(length=128), primary_key=True, nullable=False),
            sa.Column("article_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=16), nullable=False),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
            sa.Column("received_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["article_id"], ["article.id"]),
        )


def downgrade() -> None:
    op.drop_table("storageevent")
    # Storage and article may have existed before this migration and contain live data.
    # Keep those tables and the nullable inventory columns during downgrade.
