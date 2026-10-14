import asyncio

from fastapi import APIRouter, HTTPException, status

from ..workers import production_queue
from ..workers.production_queue import ProductionOrderPayload
from ..services.analytics import register_run

router = APIRouter(prefix="/productionorder", tags=["productionorder"])


@router.get("/queue-status")
async def get_production_queue_status():
    return production_queue.get_worker_status()


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_productionorder(payload: ProductionOrderPayload):
    if not production_queue.get_worker_status()["worker_running"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Production worker is not running; check /productionorder/queue-status and restart the backend.",
        )
    payload._analytics_run_id = await asyncio.to_thread(register_run, "production", payload)
    await production_queue.order_queue.put(payload)
    production_queue.logger.info("Production order %s: accepted into queue", payload.order_id)
    return {
        "queued": True,
        "order_id": payload.order_id,
        "queue_size": production_queue.order_queue.qsize(),
    }
