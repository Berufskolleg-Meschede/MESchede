from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field

from .enums import DeliveryOrderType, OrderStatus


class DeliveryOrderBase(SQLModel):
    order_number: str = Field(unique=True)
    order_type: DeliveryOrderType
    status: OrderStatus = OrderStatus.PENDING
    partner_name: str
    delivery_date: Optional[date] = None


class DeliveryOrder(DeliveryOrderBase, table=True):
    __tablename__ = "deliveryorder"
    id: int = Field(default=None, primary_key=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeliveryOrderCreate(DeliveryOrderBase):
    pass


class DeliveryOrderItemBase(SQLModel):
    delivery_order_id: int = Field(foreign_key="deliveryorder.id")
    product_id: int = Field(foreign_key="product.id")
    quantity_planned: float
    quantity_actual: float = 0.0


class DeliveryOrderItem(DeliveryOrderItemBase, table=True):
    __tablename__ = "deliveryorderitem"
    id: int = Field(default=None, primary_key=True, nullable=False)


class DeliveryOrderItemCreate(DeliveryOrderItemBase):
    pass
