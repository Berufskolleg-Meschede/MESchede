"""Persistenter Spiegel des SPS-Produktkatalogs, unabhängig von ERP-Artikelpreisen."""

from datetime import datetime

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class PlcCatalogProductRecord(SQLModel, table=True):
    """Bewahrt gelesene Produktidentität, Bauplan und letzte bestätigte Verfügbarkeit."""

    __tablename__ = "plc_catalog_product"

    product_id: int = Field(primary_key=True)
    product_text: str = Field(max_length=30)
    source_index: int | None = None
    specification: dict = Field(sa_column=Column(JSON, nullable=False))
    available: bool = True
    observed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class PlcCatalogStateRecord(SQLModel, table=True):
    """Trennt typspezifische Queue-Kapazität und Syncfehler von gespeicherten Produkten."""

    __tablename__ = "plc_catalog_state"

    order_type: str = Field(primary_key=True)
    capacity: int | None = None
    last_success_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    last_attempt_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    error: str | None = None
