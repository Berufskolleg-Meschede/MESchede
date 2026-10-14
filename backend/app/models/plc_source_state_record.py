"""Zuletzt erfolgreiche PLC-Beobachtung je Auftragsslot."""

from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class PlcSourceStateRecord(SQLModel, table=True):
    """Bewahrt Quellenfehler getrennt vom fachlichen Laufresultat."""

    __tablename__ = "plc_source_state"

    order_type: str = Field(primary_key=True)
    connection_status: str = "unknown"
    last_success_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    error: str | None = None
