from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field

from .enums import OrderStatus


class ProductionOrderBase(SQLModel):
    order_number: str = Field(unique=True)
    product_id: int = Field(foreign_key="product.id")
    machine_id: Optional[int] = Field(default=None, foreign_key="machine.id")
    quantity_planned: float
    quantity_produced: float = 0.0
    status: OrderStatus = OrderStatus.PENDING


class ProductionOrder(ProductionOrderBase, table=True):
    __tablename__ = "productionorder"
    id: int = Field(default=None, primary_key=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ProductionOrderCreate(ProductionOrderBase):
    pass
