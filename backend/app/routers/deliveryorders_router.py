"""Dauerhafte Lieferannahme und getrennte Kommissionieransichten."""

from fastapi import APIRouter, Depends, Query, status

from app.domain.order_run import OrderType
from app.models.order_dto import OrderDetailView, OrderPageView, OrderPayload
from app.routers.order_dependencies import admit_order, execute_order_operation, get_order_worker
from app.services.order_query_service import OrderQueryService
from app.workers.order_worker_host import OrderWorkerHost


router = APIRouter(prefix="/deliveryorder", tags=["deliveryorder"])


@router.get("/", response_model=OrderPageView)
async def list_deliveryorders(
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    search: str = Query("", max_length=200),
    status: str | None = Query(None, pattern="^(pending|in_progress|error|completed|review_required)$"),
    worker: OrderWorkerHost = Depends(get_order_worker),
):
    """Liefert Lieferaufträge ohne Verwechslung mit gleich nummerierten Produktionsaufträgen."""
    query = OrderQueryService(worker.repository, worker.settings)
    return await execute_order_operation(lambda: query.page(OrderType.DELIVERY, worker.running, offset, limit, search, status))


@router.get("/queue-status")
async def get_delivery_queue_status(worker: OrderWorkerHost = Depends(get_order_worker)):
    """Liest Diagnosen ohne Kontakt zur PLC."""
    return await execute_order_operation(lambda: worker.diagnostics(OrderType.DELIVERY))


@router.get("/{order_id:path}", response_model=OrderDetailView)
async def get_deliveryorder(order_id: str, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Löst eine fachliche ID innerhalb des Lieferbereichs auf."""
    query = OrderQueryService(worker.repository, worker.settings)
    return await execute_order_operation(lambda: query.detail(OrderType.DELIVERY, order_id))


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_deliveryorder(payload: OrderPayload, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Bestätigt nach Speicherung die Annahme, nicht den Kommissionierstart."""
    return await admit_order(worker, OrderType.DELIVERY, payload)
