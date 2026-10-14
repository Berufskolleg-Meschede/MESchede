"""Fachlicher Eingang für die gemeinsame dauerhafte Auftragsspeicherung."""

from app.domain.order_run import OrderType
from app.models.order_dto import OrderPayload
from app.repositories.order_repository import OrderRepository


class OrderAdmissionService:
    """Hält HTTP-Annahme und dauerhafte Speicherung an einer gemeinsamen Grenze."""

    def __init__(self, repository: OrderRepository) -> None:
        """Übernimmt die transaktionale Persistenz als Abhängigkeit."""
        self.repository = repository

    def accept(self, kind: OrderType, payload: OrderPayload) -> dict:
        """Liefert nach Commit eine Referenz, ohne einen PLC-Start zu behaupten."""
        stored = self.repository.admit(kind, payload)
        queued = self.repository.queue_size(kind)
        return {
            "queued": stored.run.phase == "queued",
            "order_id": stored.order.order_id,
            "order_ref": stored.order.id,
            "run_id": stored.run.id,
            "queue_size": queued,
            "accepted_sequence": stored.order.accepted_sequence,
        }
