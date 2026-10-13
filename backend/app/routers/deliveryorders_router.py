from fastapi import APIRouter, HTTPException, status

from ..workers import delivery_queue
from ..workers.delivery_queue import DeliveryOrderPayload

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
    existing = delivery_queue.get_accepted_order(payload.order_id)
    if existing is not None:
        if existing != payload:
            raise HTTPException(status_code=409, detail="order_id already used with a different payload")
        return {"queued": False, "duplicate": True, "order_id": payload.order_id,
                "queue_size": delivery_queue.delivery_queue.qsize()}
    if not delivery_queue.get_worker_status()["worker_running"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Delivery worker is not running; check /deliveryorder/queue-status and restart the backend.",
        )
    delivery_queue.accept_order(payload)
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
