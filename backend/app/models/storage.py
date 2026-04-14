from typing import Optional

from sqlmodel import SQLModel, Field


class StorageItemBase(SQLModel):
    product_id: int = Field(foreign_key="product.id")
    quantity: float = 0.0
    location: Optional[str] = None


class StorageItem(StorageItemBase, table=True):
    __tablename__ = "storageitem"
    id: int = Field(default=None, primary_key=True, nullable=False)


class StorageItemCreate(StorageItemBase):
    pass
