"""Kompatibilitätszugang zum gemeinsamen Auftragsworker für Produktion."""

from app.domain.order_run import OrderType
from app.models.order_dto import OrderPayload
from app.workers.order_worker_host import OrderWorkerHost


ProductionOrderPayload = OrderPayload
_host: OrderWorkerHost | None = None


def bind_worker(host: OrderWorkerHost) -> None:
    """Verbindet alte Produktionszugänge mit dem einzigen gemeinsamen Worker."""
    global _host
    _host = host


def get_worker_status() -> dict:
    """Bezieht Produktionsdiagnosen aus derselben dauerhaften Queue wie die API."""
    if _host is None:
        return {"worker_running": False, "worker_phase": "stopped", "queue_size": 0,
                "current_order_id": None, "last_order_id": None, "last_completed_order_id": None, "last_error": None}
    return _host.diagnostics(OrderType.PRODUCTION)


async def start_worker() -> None:
    """Startet nur den gebundenen gemeinsamen Worker und keine unabhängige Schleife."""
    if _host is None:
        raise RuntimeError("Der gemeinsame Auftragsworker wurde noch nicht gebunden.")
    await _host.start()


async def stop_worker() -> None:
    """Beendet den gemeinsamen Lifecycle geordnet."""
    if _host is not None:
        await _host.stop()
