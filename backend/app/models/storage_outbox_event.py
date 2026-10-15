"""Dauerhafte RabbitMQ-Ausgangsereignisse für bestätigte Lagerbewegungen."""

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, Index
from sqlmodel import Field, SQLModel


class StorageOutboxEvent(SQLModel, table=True):
    """Hält Lagerbewegungen bis zur bestätigten Veröffentlichung erneut zustellbar."""

    __tablename__ = "storage_outbox_event"
    __table_args__ = (
        CheckConstraint("quantity_delta IN (-1, 1)", name="ck_storage_outbox_unit_delta"),
        Index("ix_storage_outbox_pending", "published_at", "created_at"),
    )

    event_id: str = Field(primary_key=True, max_length=128)
    product_id: int
    quantity_delta: int
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            default=lambda: datetime.now(timezone.utc),
        )
    )
    published_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
