"""Dauerhafte Produktionsannahme und typspezifische Leseansichten."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.domain.order_run import OrderType
from app.models.order_dto import OrderPageView, OrderPayload, OrderView
from app.routers.order_dependencies import execute_order_operation, get_order_worker
from app.services.order_admission_service import OrderAdmissionService
from app.services.order_query_service import OrderQueryService
from app.workers.order_worker_host import OrderWorkerHost


router = APIRouter(prefix="/productionorder", tags=["productionorder"])


@router.get("/", response_model=OrderPageView)
async def list_productionorders(
    offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
    worker: OrderWorkerHost = Depends(get_order_worker),
):
    """Liefert nur Produktionsaufträge mit gemeinsamer globaler Reihenfolge."""
    query = OrderQueryService(worker.repository, worker.settings)
    return await execute_order_operation(lambda: query.page(OrderType.PRODUCTION, worker.running, offset, limit))


@router.get("/queue-status")
async def get_production_queue_status(worker: OrderWorkerHost = Depends(get_order_worker)):
    """Liest Diagnosen ohne Kontakt zur PLC."""
    return await execute_order_operation(lambda: worker.diagnostics(OrderType.PRODUCTION))


@router.get("/{order_id:path}", response_model=OrderView)
async def get_productionorder(order_id: str, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Löst eine fachliche ID innerhalb des Produktionsbereichs auf."""
    query = OrderQueryService(worker.repository, worker.settings)
    return await execute_order_operation(lambda: query.detail(OrderType.PRODUCTION, order_id))


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_productionorder(payload: OrderPayload, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Bestätigt nach Speicherung die Annahme, nicht den PLC-Start."""
    if not worker.running:
        raise HTTPException(503, "Der Auftragsworker ist nicht gestartet. Bitte den Backendstatus prüfen.")
    admission = OrderAdmissionService(worker.repository)
    return await execute_order_operation(lambda: admission.accept(OrderType.PRODUCTION, payload))
