"""Persistierter Ausführungsnachweis eines Auftrags."""

from datetime import datetime

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


class OrderRunRecord(SQLModel, table=True):
    """Erhält einen Lauf auch bei unklarem Start oder verlorenem Prozess."""

    __tablename__ = "order_run"
    __table_args__ = (UniqueConstraint("order_ref"),)

    id: str = Field(primary_key=True)
    order_ref: str = Field(foreign_key="mes_order.id", index=True)
    phase: str = "queued"
    version: int = 1
    review_required: bool = False
    review_reason: str | None = None
    last_observed_status: int | None = None
    result_observed: bool = False
    completion_assumed: bool = False
    manual_good_quantity: int | None = None
    manual_error_quantity: int | None = None
    has_manual_review: bool = False
    started_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    ended_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    phase_changed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
