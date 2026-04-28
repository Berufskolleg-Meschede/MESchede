from typing import Optional
from .enums import OrderStatus
from sqlmodel import Relationship
from sqlmodel import SQLModel, Field

class ProductionOrderBase(SQLModel):
    quantity: int
    status: OrderStatus = OrderStatus.PENDING
    article_id: int

class ProductionOrder(ProductionOrderBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)
    article_id: int = Field(foreign_key="article.id")

    article: Optional["Article"] = Relationship(back_populates="productionorder")
