"""Dauerhaft angenommene Aufträge mit typbezogener fachlicher Identität."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


class MesOrderRecord(SQLModel, table=True):
    """Bewahrt den normalisierten Eingang und die globale Annahmereihenfolge."""

    __tablename__ = "mes_order"
    __table_args__ = (
        UniqueConstraint("order_type", "order_id"),
        UniqueConstraint("order_type", "plc_order_number"),
        UniqueConstraint("accepted_sequence"),
    )

    id: str = Field(primary_key=True)
    order_type: str = Field(index=True)
    order_id: str
    plc_order_number: int
    accepted_sequence: int = Field(index=True)
    accepted_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
