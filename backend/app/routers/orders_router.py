"""Lesende Gesamtübersicht und ausdrücklich getrennte manuelle Laufprüfung."""

from fastapi import APIRouter, Depends

from app.models.order_dto import OverviewView, ReviewRequest, ReviewView
from app.routers.order_dependencies import execute_order_operation, get_order_worker
from app.services.order_query_service import OrderQueryService
from app.services.run_review_service import RunReviewService
from app.workers.order_worker_host import OrderWorkerHost


router = APIRouter(prefix="/orders", tags=["orders"])


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
