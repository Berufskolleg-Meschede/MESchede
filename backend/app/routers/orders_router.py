"""Lesende Gesamtübersicht und ausdrücklich getrennte manuelle Laufprüfung."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from opcua import ua

from app.models.order_dto import OverviewView, ReviewRequest, ReviewView
from app.models.order_input import OrderInputContext
from app.domain.order_run import OrderType
from app.routers.order_dependencies import execute_order_operation, get_order_worker
from app.services.order_query_service import OrderQueryService
from app.services.run_review_service import RunReviewService
from app.workers.order_worker_host import OrderWorkerHost


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/catalog/sync", response_model=OrderInputContext)
async def synchronize_product_catalog(order_type: OrderType, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Aktualisiert nur den Datenbankkatalog durch lesenden SPS-Zugriff, niemals einen Auftrag."""
    try:
        await worker.input_service.synchronize(order_type)
        return await worker.input_service.prepare(order_type, worker.running)
    except (OSError, TimeoutError, KeyError, ValueError, ua.UaError) as error:
        raise HTTPException(503, "Der SPS-Produktkatalog konnte nicht vollständig abgeglichen werden. Letzte Daten bleiben erhalten.") from error
    except SQLAlchemyError as error:
        raise HTTPException(503, "Der Produktkatalog konnte nicht gespeichert werden. Bitte die Datenbank prüfen.") from error


@router.get("/input-context", response_model=OrderInputContext)
async def get_order_input_context(order_type: OrderType, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Bereitet eine Erfassung lesend vor; Vorschläge reservieren keine Identität."""
    try:
        return await worker.input_service.prepare(order_type, worker.running)
    except SQLAlchemyError as error:
        raise HTTPException(503, "Die Auftragsdaten sind derzeit nicht erreichbar. Bitte erneut versuchen.") from error


@router.get("/overview", response_model=OverviewView)
async def get_order_overview(worker: OrderWorkerHost = Depends(get_order_worker)):
    """Liefert kombinierte gespeicherte Daten ohne PLC-Zugriff."""
    query = OrderQueryService(worker.repository, worker.settings)
    return await execute_order_operation(lambda: query.overview(worker.running))


@router.post("/runs/{run_id}/reviews", response_model=ReviewView)
async def post_run_review(run_id: str, payload: ReviewRequest, worker: OrderWorkerHost = Depends(get_order_worker)):
    """Speichert nur Laufbewertung und Mengen; die Operation besitzt keinen PLC-Gateway."""
    review = RunReviewService(worker.repository)
    return await execute_order_operation(lambda: review.review(run_id, payload))
