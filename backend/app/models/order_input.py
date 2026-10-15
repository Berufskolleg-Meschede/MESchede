"""Verträge für die lesende Erfassungsvorbereitung und feldbezogene Ablehnung."""

from datetime import date, datetime, time

from pydantic import BaseModel, Field


class CatalogProduct(BaseModel):
    """Bewahrt die aus dem Katalog gelesene Identität ohne Ableitung aus Arrayindizes."""

    product_id: int = Field(strict=True, ge=0, le=255)
    product_text: str = Field(min_length=1, max_length=30)
    source_index: int | None = Field(default=None, strict=True, ge=1)
    specification: dict[str, int | float] = Field(default_factory=dict)


CATALOG_BYTE_FIELDS = ("Gehaeuse", "Deckel", "Hoehe", "GehaeuseFarbe", "DeckelFarbe")
CATALOG_REAL_FIELDS = ("DrehmomentSoll", "HoeheMin", "HoeheMax", "DrehmomentMin", "DrehmomentMax", "GewichtMin", "GewichtMax")


class OrderCatalog(BaseModel):
    """Verbindet gültige Produkte mit der beobachteten Kapazität eines Auftragsslots."""

    products: list[CatalogProduct] = Field(min_length=1)
    capacity: int = Field(strict=True, ge=1, le=255)
    observed_at: datetime


class OrderInputContext(BaseModel):
    """Liefert Vorschläge und Voraussetzungen, ohne Aufträge oder Nummern zu reservieren."""

    available: bool
    suggested_order_id: str | None
    suggested_plc_order_number: int | None
    start_date: date
    start_time: time
    plant_timezone: str
    products: list[CatalogProduct]
    capacity: int | None
    observed_at: datetime | None
    error: str | None
    refresh_interval_s: float
    stale_after_s: float


class OrderInputError(ValueError):
    """Transportiert deutsche Fehlermeldungen mit bestehenden Payload-Feldpfaden."""

    def __init__(self, path: tuple, message: str) -> None:
        """Bewahrt den Feldbezug für die HTTP- und Formulargrenze."""
        super().__init__(message)
        self.path = path
