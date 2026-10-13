"""Abgleich dauerhaft offener Läufe vor einer weiteren Anlagenübergabe."""

from app.domain.order_run import OrderType, RunPhase
from app.domain.plc_snapshot import PlcSnapshot
from app.repositories.order_repository import OrderRepository, StoredOrder


class OrderRecoveryService:
    """Unterscheidet beweisbar ungestartete Vorbereitung und unklaren Start."""

    def __init__(self, repository: OrderRepository) -> None:
        """Übernimmt die dauerhaft gespeicherte Laufreservierung."""
        self.repository = repository

    def reconcile(self, stored: StoredOrder, snapshots: dict[OrderType, PlcSnapshot]) -> None:
        """Lässt einen aktiven korrelierten Lauf stehen und markiert Unklarheit zur Prüfung."""
        if stored.run.review_required:
            return
        ready = len(snapshots) == len(OrderType) and all(item.ready for item in snapshots.values())
        if stored.run.phase == RunPhase.PREPARING.value:
            if ready:
                self.repository.return_prepared_to_queue(stored.run.id)
            else:
                self.repository.require_review(stored.run.id, "Die Anlage ist nach der Vorbereitung nicht eindeutig bereit.")
            return
        if stored.run.phase in {RunPhase.COMPLETED.value, RunPhase.INTERRUPTED.value}:
            return
        observation = snapshots.get(OrderType(stored.order.order_type))
        if observation is None or observation.order_number != stored.order.plc_order_number:
            self.repository.require_review(stored.run.id, "Der unterbrochene Lauf ist nicht eindeutig zugeordnet.")
        elif observation.ready and stored.run.phase != RunPhase.AWAITING_RESET.value:
            self.repository.require_review(stored.run.id, "Die PLC ist Idle, aber ein Laufabschluss ist nicht belegt.")
