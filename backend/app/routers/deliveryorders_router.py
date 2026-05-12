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