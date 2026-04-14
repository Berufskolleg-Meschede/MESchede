from typing import Optional

from sqlmodel import SQLModel, Field

from .enums import ProductUnit


class ProductBase(SQLModel):
    product_number: str = Field(unique=True)
    name: str
    description: Optional[str] = None
    unit: ProductUnit = ProductUnit.PIECE


class Product(ProductBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)


class ProductCreate(ProductBase):
    pass
