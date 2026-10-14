"""Historie expliziter manueller Laufbewertungen."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, JSON
from sqlmodel import Field, SQLModel


class RunReviewRecord(SQLModel, table=True):
    """Erkennt wiederholte Reviewanforderungen und bewahrt deren ursprünglichen Inhalt."""

    __tablename__ = "run_review"

    request_id: str = Field(primary_key=True)
    run_id: str = Field(foreign_key="order_run.id", index=True)
    outcome: str
    good_quantity: int | None = None
    error_quantity: int | None = None
    reviewed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    request_payload: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
