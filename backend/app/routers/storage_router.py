from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db import get_session
from app.models.storage import (
    Storage,
    StorageBase
)

router = APIRouter(
    prefix="/storage",
    tags=["storage"]
)


@router.get("/", response_model=list[Storage])
async def list_storage(
    session: AsyncSession = Depends(get_session)
):
    result = await session.exec(
        select(Storage)
    )

    return result.all()


@router.get("/{item_id}", response_model=Storage)
async def get_storage(
    item_id: int,
    session: AsyncSession = Depends(get_session)
):
    storage = await session.get(
        Storage,
        item_id
    )

    if not storage:
        raise HTTPException(
            status_code=404,
            detail="Storage item not found"
        )

    return storage


@router.post("/", response_model=Storage)
async def post_storage(
    storage: StorageBase,
    session: AsyncSession = Depends(get_session)
):
    db_storage = Storage(
        **storage.model_dump()
    )

    session.add(db_storage)

    await session.commit()
    await session.refresh(db_storage)

    return db_storage


@router.patch("/{item_id}", response_model=Storage)
async def patch_storage(
    item_id: int,
    updated_data: StorageBase,
    session: AsyncSession = Depends(get_session)
):
    storage = await session.get(
        Storage,
        item_id
    )

    if not storage:
        raise HTTPException(
            status_code=404,
            detail="Storage item not found"
        )

    update_data = updated_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(storage, key, value)

    session.add(storage)

    await session.commit()
    await session.refresh(storage)

    return storage


@router.patch("/{item_id}/{amount}",
              response_model=Storage)
async def add_storage_amount(
    item_id: int,
    amount: int,
    session: AsyncSession = Depends(get_session)
):
    storage = await session.get(
        Storage,
        item_id
    )

    if not storage:
        raise HTTPException(
            status_code=404,
            detail="Storage item not found"
        )

    storage.quantity += amount

    if storage.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative"
        )

    session.add(storage)

    await session.commit()
    await session.refresh(storage)

    return storage