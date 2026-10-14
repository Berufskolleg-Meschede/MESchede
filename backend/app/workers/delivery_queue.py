"""Kompatibilitätszugang zum gemeinsamen Auftragsworker für Lieferung."""

from app.domain.order_run import OrderType
from app.models.order_dto import OrderPayload
from app.workers.order_worker_host import OrderWorkerHost


DeliveryOrderPayload = OrderPayload
_host: OrderWorkerHost | None = None


def bind_worker(host: OrderWorkerHost) -> None:
    """Verbindet alte Lieferzugänge mit dem einzigen gemeinsamen Worker."""
    global _host
    _host = host


def get_worker_status() -> dict:
    """Bezieht Lieferdiagnosen aus derselben dauerhaften Queue wie die API."""
    if _host is None:
        return {"worker_running": False, "worker_phase": "stopped", "queue_size": 0,
                "current_order_id": None, "last_order_id": None, "last_completed_order_id": None, "last_error": None}
    return _host.diagnostics(OrderType.DELIVERY)


def get_current_delivery_order_id() -> str | None:
    """Erhält den bestehenden Settings-Endpunkt trotz gemeinsamem Worker."""
    return get_worker_status().get("current_order_id")


async def start_delivery_worker() -> None:
    """Startet nur den gebundenen gemeinsamen Worker und keine zweite Startvergabe."""
    if _host is None:
        raise RuntimeError("Der gemeinsame Auftragsworker wurde noch nicht gebunden.")
    await _host.start()


async def stop_delivery_worker() -> None:
    """Beendet denselben gemeinsamen Lifecycle wie der Produktionszugang."""
    if _host is not None:
        await _host.stop()
