from fastapi import APIRouter, status

from ..workers.production_queue import ProductionOrderPayload, order_queue

router = APIRouter(prefix="/productionorder", tags=["productionorder"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_productionorder(payload: ProductionOrderPayload):
    await order_queue.put(payload)
    return {
        "queued": True,
        "order_id": payload.order_id,
        "queue_size": order_queue.qsize(),
    }