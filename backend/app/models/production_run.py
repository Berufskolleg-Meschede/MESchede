from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ProductionRun(SQLModel, table=True):
    """One durable MES run, linked to a distinct production or delivery order."""

    id: Optional[int] = Field(default=None, primary_key=True)
    order_type: str = Field(max_length=16, index=True)
    order_id: str = Field(max_length=128)
    plc_order_number: Optional[int] = Field(default=None)
    planned_quantity: Optional[int] = Field(default=None)
    processed_quantity: Optional[int] = Field(default=None)
    good_quantity: Optional[int] = Field(default=None)
    defective_quantity: Optional[int] = Field(default=None)
    status: str = Field(default="queued", max_length=24)
    started_at: Optional[datetime] = Field(default=None)
    ended_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    last_observed_at: Optional[datetime] = Field(default=None)
    last_error_type: Optional[str] = Field(default=None, max_length=128)


class ProductionRunRead(SQLModel):
    id: int
    order_type: str
    order_id: str
    plc_order_number: Optional[int]
    planned_quantity: Optional[int]
    processed_quantity: Optional[int]
    good_quantity: Optional[int]
    defective_quantity: Optional[int]
    status: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    created_at: datetime
    last_observed_at: Optional[datetime]
    last_error_type: Optional[str]
