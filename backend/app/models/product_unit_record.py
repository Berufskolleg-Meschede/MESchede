"""Geplante Einheit und ihr final belegtes Produktresultat."""

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, SQLModel


class ProductUnitRecord(SQLModel, table=True):
    """Upsert-Schlüssel bleibt an den korrelierten Lauf und Queueplatz gebunden."""

    __tablename__ = "product_unit"
    __table_args__ = (
        UniqueConstraint("run_id", "queue_index"),
        CheckConstraint("result IS NULL OR result IN ('good', 'failed')"),
    )

    id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="order_run.id", index=True)
    queue_index: int
    product_id: int
    product_text: str
    serial_number: int
    sequence_number: int
    result: str | None = None
    raw_status: int | None = None
    error_code: int | None = None
