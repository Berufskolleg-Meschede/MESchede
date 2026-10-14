"""Gemeinsamer HTTP-Vertrag für Produktions-, Liefer- und Reviewansichten."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.order_run import OrderType, ReviewOutcome, RunPhase
from app.models.mes_auftrag import MESAuftrag


Quantity = Annotated[int, Field(strict=True, ge=0)]


class OrderPayload(BaseModel):
    """Übernimmt den vorhandenen PLC-nahen Eingabevertrag."""

    order_id: str = Field(min_length=1, max_length=200, pattern=r".*\S.*")
    mes_auftrag: MESAuftrag

    @field_validator("order_id")
    @classmethod
    def normalize_order_id(cls, value: str) -> str:
        """Verwendet für Idempotenz und PLC-Zuordnung eine kanonische Auftrags-ID."""
        return value.strip()


class SourceStatus(BaseModel):
    """Kennzeichnet Quellenzustand und echte erfolgreiche Beobachtungen."""

    connection_status: Literal["connected", "disconnected", "unknown"] = "unknown"
    last_success_at: datetime | None = None
    freshness: Literal["fresh", "stale", "unknown"] = "unknown"
    error: str | None = None


class ProductUnitView(BaseModel):
    """Zeigt geplante Einheiten und ausschließlich tatsächlich beobachtete Ergebnisse."""

    index: int
    product_id: int
    product_text: str
    serial_number: int | None
    sequence_number: int | None
    result: Literal["good", "failed"] | None = None
    raw_status: int | None = None
    error_code: int | None = None


class OrderView(BaseModel):
    """Liefert einen dauerhaft identifizierten Auftrag samt Lauf und Mengenherkunft."""

    order_id: str
    order_type: OrderType
    order_ref: str
    run_id: str
    plc_order_number: int
    accepted_sequence: int
    accepted_at: datetime
    status: str
    run_phase: RunPhase
    planned_quantity: int
    processed_quantity: int | None
    good_quantity: int | None
    error_quantity: int | None
    result_complete: bool
    quantity_source: Literal["plc", "completion", "manual", "mixed", "unknown"]
    review_required: bool
    review_reason: str | None
    has_manual_review: bool
    queue_position: int | None
    version: int
    started_at: datetime | None
    ended_at: datetime | None
    source: SourceStatus
    units: list[ProductUnitView]


class ReviewRequest(BaseModel):
    """Erfasst Laufbewertung und bekannte Mengen ohne erforderliche Erklärung."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    expected_version: Annotated[int, Field(strict=True, ge=1)]
    outcome: ReviewOutcome
    good_quantity: Quantity | None = None
    error_quantity: Quantity | None = None


class ReviewView(BaseModel):
    """Bewahrt die gespeicherte Bewertung einschließlich Versionsbezug."""

    request_id: str
    run_id: str
    outcome: ReviewOutcome
    good_quantity: int | None
    error_quantity: int | None
    reviewed_at: datetime


class DispatchView(BaseModel):
    """Zeigt den gemeinsamen Sperrgrund und den reservierten Lauf."""

    blocked: bool
    reason: str | None
    active_run_id: str | None
    worker_running: bool


class OrderSummary(BaseModel):
    """Summiert Auftragszustände; Mengen fehlen bei unvollständiger Beobachtung."""

    total: int
    pending: int
    in_progress: int
    completed: int
    error: int
    review_required: int


class OverviewView(BaseModel):
    """Kombiniert beide Bereiche aus einem konsistenten Datenbanksnapshot."""

    production: OrderSummary
    delivery: OrderSummary
    combined: OrderSummary
    dispatch: DispatchView
    sources: dict[OrderType, SourceStatus]
    reviews: list[OrderView]
    active: list[OrderView]
    waiting: list[OrderView]
    refresh_interval_s: float
    stale_after_s: float


class OrderPageView(BaseModel):
    """Stellt Liste und Warte-/Aktivansicht für genau eine Auftragsart bereit."""

    orders: list[OrderView]
    total: int
    filtered_total: int
    offset: int
    limit: int
    active: list[OrderView]
    waiting: list[OrderView]
    reviews: list[OrderView]
    summary: OrderSummary
    dispatch: DispatchView
    source: SourceStatus
    refresh_interval_s: float
    stale_after_s: float
