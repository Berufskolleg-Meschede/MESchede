from datetime import date, timezone
from typing import Literal

from fastapi import APIRouter, Query

from app.models.production_run import ProductionRunRead
from app.services.analytics import list_runs

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/", response_model=list[ProductionRunRead])
def get_runs(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    order_type: Literal["production", "delivery"] | None = None,
):
    runs = list_runs(from_date, to_date, order_type)
    for run in runs:
        for field in ("created_at", "started_at", "ended_at", "last_observed_at"):
            value = getattr(run, field)
            if value is not None and value.tzinfo is None:
                setattr(run, field, value.replace(tzinfo=timezone.utc))
    return runs
