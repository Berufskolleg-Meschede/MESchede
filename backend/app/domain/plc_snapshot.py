"""Bibliotheksunabhängige Beobachtungen beider PLC-Auftragsslots."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.order_run import OrderType


@dataclass(frozen=True)
class ProductObservation:
    """Erhält nur vom Server gelesene Felder einer Queueeinheit."""

    index: int
    product_id: int | None
    serial_number: int | None
    sequence_number: int | None
    raw_status: int | None
    error_code: int | None


@dataclass(frozen=True)
class PlcSnapshot:
    """Verbindet eine konsistent gelesene Auftragsidentität mit ihrem Feedback."""

    order_type: OrderType
    order_number: int
    command: int
    status: int
    observed_at: datetime
    products: tuple[ProductObservation, ...] = ()
    product_count: int = 0

    @property
    def ready(self) -> bool:
        """Belegt Idle anhand von Kommando und MES-Feedback gemeinsam."""
        return self.command == 0 and self.status == 0 and self.product_count == 0
