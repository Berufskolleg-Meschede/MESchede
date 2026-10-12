<<<<<<< HEAD
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
    if not delivery_queue.get_worker_status()["worker_running"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Delivery worker is not running; check /deliveryorder/queue-status and restart the backend.",
        )
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

=======
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_session
from app.models.delivery_order import DeliveryOrder, DeliveryOrderBase

router = APIRouter(
    prefix="/deliveryorder",
    tags=["deliveryorder"]
)

# GET ALL
@router.get("/", response_model=list[DeliveryOrder])
async def list_deliveryorders(
    session: AsyncSession = Depends(get_session)
):
    result = await session.exec(
        select(DeliveryOrder)
    )

    return result.all()


# GET ONE
@router.get("/{deliveryorder_id}", response_model=DeliveryOrder)
async def get_deliveryorder(
    deliveryorder_id: int,
    session: AsyncSession = Depends(get_session)
):
    deliveryorder = await session.get(
        DeliveryOrder,
        deliveryorder_id
    )
>>>>>>> origin/main

    if not deliveryorder:
        raise HTTPException(
            status_code=404,
            detail="DeliveryOrder not found"
        )

    return deliveryorder


# CREATE
@router.post("/", response_model=DeliveryOrder)
async def post_deliveryorder(
    deliveryorder: DeliveryOrderBase,
    session: AsyncSession = Depends(get_session)
):
    db_deliveryorder = DeliveryOrder(
        **deliveryorder.model_dump()
    )

    session.add(db_deliveryorder)

    await session.commit()
    await session.refresh(db_deliveryorder)

    return db_deliveryorder


# UPDATE
@router.patch("/{deliveryorder_id}", response_model=DeliveryOrder)
async def patch_deliveryorder(
    deliveryorder_id: int,
    updated_data: DeliveryOrderBase,
    session: AsyncSession = Depends(get_session)
):
    deliveryorder = await session.get(
        DeliveryOrder,
        deliveryorder_id
    )

    if not deliveryorder:
        raise HTTPException(
            status_code=404,
            detail="DeliveryOrder not found"
        )

    update_data = updated_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(deliveryorder, key, value)

    session.add(deliveryorder)

    await session.commit()
    await session.refresh(deliveryorder)

    return deliveryorder


# DELETE
@router.delete("/{deliveryorder_id}")
<<<<<<< HEAD
def delete_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")
=======
async def delete_deliveryorder(
    deliveryorder_id: int,
    session: AsyncSession = Depends(get_session)
):
    deliveryorder = await session.get(
        DeliveryOrder,
        deliveryorder_id
    )

    if not deliveryorder:
        raise HTTPException(
            status_code=404,
            detail="DeliveryOrder not found"
        )

    await session.delete(deliveryorder)

    await session.commit()

    return {
        "message": "DeliveryOrder deleted"
    }
>>>>>>> origin/main
