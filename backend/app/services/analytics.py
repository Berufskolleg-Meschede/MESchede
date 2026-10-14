"""Durable run observations and read models for the production analytics page."""

from datetime import date, datetime, time, timezone
import logging

from sqlalchemy import select, update, func, case

from app.db.session import SessionLocal
from app.models.production_run import ProductionRun
from app.models.mes_order import MesOrderRecord
from app.models.order_run_record import OrderRunRecord
from app.models.product_unit_record import ProductUnitRecord

logger = logging.getLogger(__name__)


def _naive_utc(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def register_run(order_type: str, payload) -> int:
    """Persist one accepted run and return its unique run ID."""
    order_id = payload.order_id.strip()
    if not order_id:
        raise ValueError("order_id darf nicht leer sein.")
    payload.order_id = order_id

    with SessionLocal() as session:
        run = ProductionRun(
            order_type=order_type,
            order_id=order_id,
            plc_order_number=payload.mes_auftrag.kopf.Auftragsnummer,
            planned_quantity=len(payload.mes_auftrag.inhalt.Produktqueue),
            status="queued",
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        if run.id is None:
            raise RuntimeError("Die Analyselauf-ID konnte nicht erzeugt werden.")
        return run.id


def observe_run_started(run_id: int | None, observed_at: datetime) -> None:
    if run_id is None:
        return
    try:
        with SessionLocal() as session:
            run = session.execute(
                select(ProductionRun).where(
                    ProductionRun.id == run_id,
                )
            ).scalars().first()
            if run is None or run.ended_at is not None:
                return
            observed_at = _naive_utc(observed_at)
            if run.started_at is None:
                run.started_at = observed_at
            run.status = "running"
            run.last_observed_at = max(run.last_observed_at or observed_at, observed_at)
            run.last_error_type = None
            session.add(run)
            session.commit()
    except Exception:
        logger.exception("Could not persist observed start for run %s", run_id)


def observe_run_completed(run_id: int | None, observed_at: datetime) -> None:
    if run_id is None:
        return
    try:
        with SessionLocal() as session:
            run = session.execute(
                select(ProductionRun).where(
                    ProductionRun.id == run_id,
                )
            ).scalars().first()
            if run is None:
                return
            observed_at = _naive_utc(observed_at)
            if run.started_at is not None and observed_at < run.started_at:
                logger.warning("Ignoring out-of-order completion for run %s", run_id)
                return
            if run.ended_at is None:
                run.ended_at = observed_at
            run.status = "completed"
            run.last_observed_at = max(run.last_observed_at or observed_at, observed_at)
            run.last_error_type = None
            session.add(run)
            session.commit()
    except Exception:
        logger.exception("Could not persist observed completion for run %s", run_id)


def observe_run_error(run_id: int | None, error_type: str) -> None:
    if run_id is None:
        return
    try:
        with SessionLocal() as session:
            run = session.execute(
                select(ProductionRun).where(
                    ProductionRun.id == run_id,
                )
            ).scalars().first()
            if run is None or run.ended_at is not None:
                return
            run.status = "unknown"
            run.last_error_type = error_type[:128]
            run.last_observed_at = _naive_utc()
            session.add(run)
            session.commit()
    except Exception:
        logger.exception("Could not persist error state for run %s", run_id)


def list_runs(
    from_date: date | None,
    to_date: date | None,
    order_type: str | None,
) -> list[dict]:
    statement = select(ProductionRun)
    observed_day = func.coalesce(ProductionRun.started_at, ProductionRun.created_at)
    if from_date is not None:
        statement = statement.where(
            observed_day >= datetime.combine(
                from_date, time.min, tzinfo=timezone.utc
            ).replace(tzinfo=None)
        )
    if to_date is not None:
        statement = statement.where(
            observed_day < datetime.combine(
                date.fromordinal(to_date.toordinal() + 1),
                time.min,
                tzinfo=timezone.utc,
            ).replace(tzinfo=None)
        )
    if order_type is not None:
        statement = statement.where(ProductionRun.order_type == order_type)
    statement = statement.order_by(ProductionRun.created_at.desc(), ProductionRun.id.desc())
    with SessionLocal() as session:
        legacy = list(session.execute(statement).scalars().all())
        current_statement = select(
            MesOrderRecord, OrderRunRecord,
            func.count(ProductUnitRecord.id).label("planned"),
            func.sum(case((ProductUnitRecord.result == "good", 1), else_=0)).label("good"),
            func.sum(case((ProductUnitRecord.result == "failed", 1), else_=0)).label("failed"),
        ).join(OrderRunRecord, OrderRunRecord.order_ref == MesOrderRecord.id).outerjoin(
            ProductUnitRecord, ProductUnitRecord.run_id == OrderRunRecord.id,
        )
        if order_type is not None:
            current_statement = current_statement.where(MesOrderRecord.order_type == order_type)
        observed_day = func.coalesce(OrderRunRecord.started_at, MesOrderRecord.accepted_at)
        if from_date is not None:
            current_statement = current_statement.where(observed_day >= datetime.combine(from_date, time.min, tzinfo=timezone.utc))
        if to_date is not None:
            current_statement = current_statement.where(observed_day < datetime.combine(date.fromordinal(to_date.toordinal() + 1), time.min, tzinfo=timezone.utc))
        current_statement = current_statement.group_by(MesOrderRecord.id, OrderRunRecord.id).order_by(observed_day.desc())
        current = session.execute(current_statement).all()
        rows = []
        current_keys = {(order.order_type, order.order_id) for order, *_ in current}
        for run in legacy:
            if (run.order_type, run.order_id) in current_keys:
                continue
            if run.good_quantity is not None and run.defective_quantity is not None:
                run.processed_quantity = run.good_quantity + run.defective_quantity
            rows.append(run.model_dump())
        for order, run, planned, good, failed in current:
            status = (
                "review_required" if run.review_required else
                "unknown" if run.phase == "interrupted" else
                "completed" if run.phase in {"completed", "completion_observed", "awaiting_reset"} else
                "running" if run.started_at else "queued"
            )
            rows.append({
                "id": -order.accepted_sequence, "order_type": order.order_type, "order_id": order.order_id,
                "plc_order_number": order.plc_order_number, "planned_quantity": planned,
                "processed_quantity": (good or 0) + (failed or 0) if run.result_observed else None,
                "good_quantity": (good or 0) if run.result_observed else None,
                "defective_quantity": (failed or 0) if run.result_observed else None,
                "status": status, "started_at": run.started_at, "ended_at": run.ended_at,
                "created_at": order.accepted_at, "last_observed_at": run.ended_at or run.started_at,
                "last_error_type": run.review_reason if run.review_required else None,
            })
        return sorted(rows, key=lambda row: _naive_utc(row["started_at"] or row["created_at"]), reverse=True)


def mark_interrupted_runs_unknown() -> None:
    """Mark in-memory queue entries interrupted by a previous backend process."""
    with SessionLocal() as session:
        session.execute(
            update(ProductionRun)
            .where(ProductionRun.status.in_(("queued", "running")))
            .values(
                status="unknown",
                last_error_type="BackendRestart",
                last_observed_at=_naive_utc(),
            )
        )
        session.commit()
