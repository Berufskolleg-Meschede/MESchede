from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_session
from app.models.production_order import (
    ProductionOrder,
    ProductionOrderBase
)

router = APIRouter(
    prefix="/productionorder",
    tags=["productionorder"]
)


@router.get("/", response_model=list[ProductionOrder])
async def list_productionorders(
    session: AsyncSession = Depends(get_session)
):
    result = await session.exec(
        select(ProductionOrder)
    )

    return result.all()


@router.get(
    "/{productionorder_id}",
    response_model=ProductionOrder
)
async def get_productionorder(
    productionorder_id: int,
    session: AsyncSession = Depends(get_session)
):
    productionorder = await session.get(
        ProductionOrder,
        productionorder_id
    )

    if not productionorder:
        raise HTTPException(
            status_code=404,
            detail="ProductionOrder not found"
        )

    return productionorder


@router.post(
    "/",
    response_model=ProductionOrder
)
async def post_productionorder(
    productionorder: ProductionOrderBase,
    session: AsyncSession = Depends(get_session)
):
    db_productionorder = ProductionOrder(
        **productionorder.model_dump()
    )

    session.add(db_productionorder)

    await session.commit()
    await session.refresh(db_productionorder)

    return db_productionorder


@router.patch(
    "/{productionorder_id}",
    response_model=ProductionOrder
)
async def patch_productionorder(
    productionorder_id: int,
    updated_data: ProductionOrderBase,
    session: AsyncSession = Depends(get_session)
):
    productionorder = await session.get(
        ProductionOrder,
        productionorder_id
    )

    if not productionorder:
        raise HTTPException(
            status_code=404,
            detail="ProductionOrder not found"
        )

    update_data = updated_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(productionorder, key, value)

    session.add(productionorder)

    await session.commit()
    await session.refresh(productionorder)

    return productionorder


@router.delete("/{productionorder_id}")
async def delete_productionorder(
    productionorder_id: int,
    session: AsyncSession = Depends(get_session)
):
    productionorder = await session.get(
        ProductionOrder,
        productionorder_id
    )

    if not productionorder:
        raise HTTPException(
            status_code=404,
            detail="ProductionOrder not found"
        )

    await session.delete(productionorder)

    await session.commit()

    return {
        "message": "ProductionOrder deleted"
    }