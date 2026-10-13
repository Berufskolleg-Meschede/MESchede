import asyncio

from fastapi import APIRouter, HTTPException, status

from ..workers import delivery_queue
from ..workers.delivery_queue import DeliveryOrderPayload
from ..services.analytics import register_run

router = APIRouter(prefix="/deliveryorder", tags=["deliveryorder"])


@router.get("/")
def list_deliveryorders():
    raise NotImplementedError("Method not implemented yet.")


@router.get("/queue-status")
async def get_delivery_queue_status():
    return delivery_queue.get_worker_status()


@router.get("/{deliveryorder_id}")
def get_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_deliveryorder(payload: DeliveryOrderPayload):
    if not delivery_queue.get_worker_status()["worker_running"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Delivery worker is not running; check /deliveryorder/queue-status and restart the backend.",
        )
    payload._analytics_run_id = await asyncio.to_thread(register_run, "delivery", payload)
    await delivery_queue.delivery_queue.put(payload)
    delivery_queue.logger.info("Delivery order %s: accepted into queue", payload.order_id)
    return {
        "queued": True,
        "order_id": payload.order_id,
        "queue_size": delivery_queue.delivery_queue.qsize(),
    }


@router.patch("/{deliveryorder_id}")
def patch_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")


@router.delete("/{deliveryorder_id}")
def delete_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")
