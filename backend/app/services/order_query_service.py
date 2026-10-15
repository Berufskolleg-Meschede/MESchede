"""Konsistente Leseansichten mit getrenntem Quellenzustand und Mengenherkunft."""

from datetime import timezone

from app.domain.order_run import OrderRun, OrderType, RunPhase
from app.models.order_dto import (
    DispatchView, OrderDetailView, OrderPageView, OrderSummary, OrderView, OverviewView, ProductUnitView, SourceStatus,
)
from app.models.plc_source_state_record import PlcSourceStateRecord
from app.repositories.order_repository import OrderRepository, StoredOrder
from app.settings import OrderSettings


class OrderQueryService:
    """Stellt Aufträge ausschließlich aus gespeicherten Fakten dar."""

    def __init__(self, repository: OrderRepository, settings: OrderSettings) -> None:
        """Übernimmt Persistenz und dieselben Aktualitätsgrenzen wie der Worker."""
        self.repository = repository
        self.settings = settings

    def _source(self, source: PlcSourceStateRecord) -> SourceStatus:
        """Markiert auch einen verbundenen, aber nicht mehr aktuellen Snapshot als veraltet."""
        freshness = "unknown"
        if source.last_success_at is not None:
            instant = source.last_success_at.replace(tzinfo=timezone.utc)
            age = (self.repository.clock() - instant).total_seconds()
            freshness = "fresh" if age <= self.settings.stale_after_s else "stale"
        return SourceStatus(
            connection_status=source.connection_status, last_success_at=source.last_success_at,
            freshness=freshness, error=source.error,
        )

    def _quantities(self, stored: StoredOrder) -> tuple[int | None, int | None, str]:
        """Ersetzt mit manuellen Gesamtmengen keine Einzelresultate und addiert nicht doppelt."""
        run = stored.run
        good = sum(unit.result == "good" for unit in stored.units) if run.result_observed else None
        failed = sum(unit.result == "failed" for unit in stored.units) if run.result_observed else None
        manual = run.manual_good_quantity is not None or run.manual_error_quantity is not None
        if run.manual_good_quantity is not None:
            good = run.manual_good_quantity
        if run.manual_error_quantity is not None:
            failed = run.manual_error_quantity
        origin = "mixed" if manual and run.result_observed else "manual" if manual else "completion" if run.completion_assumed else "plc" if run.result_observed else "unknown"
        return good, failed, origin

    def _view(self, stored: StoredOrder, source: SourceStatus, position: int | None) -> OrderView:
        """Bildet einen Lauf ohne fiktive Resultate oder erfundene PLC-Zeitpunkte ab."""
        order, run = stored.order, stored.run
        good, failed, origin = self._quantities(stored)
        processed = good + failed if good is not None and failed is not None else None
        planned_quantity = len(stored.units)
        if not stored.units:
            planned_quantity = len(order.payload.get("inhalt", {}).get("Produktqueue", []))
        return OrderView(
            order_id=order.order_id, order_type=order.order_type, order_ref=order.id,
            run_id=run.id, plc_order_number=order.plc_order_number,
            accepted_sequence=order.accepted_sequence, accepted_at=order.accepted_at,
            status=OrderRun(RunPhase(run.phase)).status, run_phase=run.phase,
            planned_quantity=planned_quantity, processed_quantity=processed,
            good_quantity=good, error_quantity=failed,
            result_complete=bool(stored.units) and all(unit.result is not None for unit in stored.units),
            quantity_source=origin, review_required=run.review_required, review_reason=run.review_reason,
            has_manual_review=run.has_manual_review, queue_position=position, version=run.version,
            started_at=run.started_at, ended_at=run.ended_at, source=source,
            units=[ProductUnitView(
                index=unit.queue_index, product_id=unit.product_id, product_text=unit.product_text,
                serial_number=unit.serial_number, sequence_number=unit.sequence_number,
                result=unit.result, raw_status=unit.raw_status, error_code=unit.error_code,
            ) for unit in stored.units],
        )

    def _summary(self, orders: list[OrderView]) -> OrderSummary:
        """Summiert fachliche Auftragszustände unabhängig von UI-Suchfiltern."""
        return OrderSummary(total=len(orders), **{
            status: sum(order.status == status for order in orders)
            for status in ("pending", "in_progress", "completed", "error", "review_required")
        })

    def _summary_from_counts(self, counts: dict[str, int]) -> OrderSummary:
        """Mappt persistierte Laufphasen auf Summen, ohne Auftragsdetails zu laden."""
        phases = {
            "pending": [RunPhase.QUEUED.value],
            "in_progress": [RunPhase.PREPARING.value, RunPhase.START_PENDING.value, RunPhase.RUNNING.value],
            "completed": [RunPhase.COMPLETED.value, RunPhase.COMPLETION_OBSERVED.value, RunPhase.AWAITING_RESET.value],
            "error": [RunPhase.INTERRUPTED.value],
            "review_required": [RunPhase.REVIEW_REQUIRED.value],
        }
        totals = {name: sum(counts.get(phase, 0) for phase in names) for name, names in phases.items()}
        return OrderSummary(total=sum(totals.values()), **totals)

    def overview(self, worker_running: bool) -> OverviewView:
        """Kombiniert beide Bereiche aus einer einzigen Datenbankbeobachtung."""
        snapshot, counts = self.repository.overview_snapshot()
        sources = {OrderType(item.order_type): self._source(item) for item in snapshot.sources}
        waiting_rows = [item for item in snapshot.orders if item.run.phase == RunPhase.QUEUED.value]
        positions = {item.run.id: index + 1 for index, item in enumerate(waiting_rows)}
        views = [self._view(item, sources[OrderType(item.order.order_type)], positions.get(item.run.id))
                 for item in snapshot.orders]
        reviews = [order for order in views if order.review_required]
        combined: dict[str, int] = {}
        for summary in counts.values():
            for phase, count in summary.items():
                combined[phase] = combined.get(phase, 0) + count
        reason = snapshot.dispatch.blocked_reason
        if not worker_running:
            reason = "Der Auftragsworker ist nicht gestartet."
        return OverviewView(
            production=self._summary_from_counts(counts.get(OrderType.PRODUCTION.value, {})),
            delivery=self._summary_from_counts(counts.get(OrderType.DELIVERY.value, {})),
            combined=self._summary_from_counts(combined),
            dispatch=DispatchView(
                blocked=bool(reason or reviews or snapshot.dispatch.active_run_id), reason=reason,
                active_run_id=snapshot.dispatch.active_run_id, worker_running=worker_running,
            ),
            sources=sources, reviews=reviews,
            active=[order for order in views if order.run_id == snapshot.dispatch.active_run_id],
            waiting=[order for order in views if order.run_phase == RunPhase.QUEUED],
            refresh_interval_s=self.settings.refresh_interval_s, stale_after_s=self.settings.stale_after_s,
        )

    def page(self, kind: OrderType, worker_running: bool, offset: int = 0, limit: int = 50,
             search: str = "", status: str | None = None) -> OrderPageView:
        """Liefert paginierte Aufträge mit ungefilterter Bereichszusammenfassung."""
        snapshot, selected_ids, total, filtered_total, counts = self.repository.page_snapshot(
            kind, offset, limit, search, status,
        )
        sources = {OrderType(item.order_type): self._source(item) for item in snapshot.sources}
        waiting = [item for item in snapshot.orders if item.run.phase == RunPhase.QUEUED.value]
        positions = {item.run.id: index + 1 for index, item in enumerate(waiting)}
        views_by_id = {
            item.run.id: self._view(item, sources[OrderType(item.order.order_type)], positions.get(item.run.id))
            for item in snapshot.orders
        }
        views = [views_by_id[run_id] for run_id in selected_ids]
        all_views = list(views_by_id.values())
        total_summary = OrderSummary(total=total, **{
            name: sum(counts.get(phase, 0) for phase in phase_names)
            for name, phase_names in {
                "pending": [RunPhase.QUEUED.value],
                "in_progress": [RunPhase.PREPARING.value, RunPhase.START_PENDING.value, RunPhase.RUNNING.value],
                "completed": [RunPhase.COMPLETED.value, RunPhase.COMPLETION_OBSERVED.value, RunPhase.AWAITING_RESET.value],
                "error": [RunPhase.INTERRUPTED.value],
                "review_required": [RunPhase.REVIEW_REQUIRED.value],
            }.items()
        })
        reason = snapshot.dispatch.blocked_reason if worker_running else "Der Auftragsworker ist nicht gestartet."
        return OrderPageView(
            orders=views, total=total, filtered_total=filtered_total, offset=offset, limit=limit,
            active=[item for item in all_views if item.run_id == snapshot.dispatch.active_run_id],
            waiting=[item for item in all_views if item.run_phase == RunPhase.QUEUED],
            reviews=[item for item in all_views if item.review_required], summary=total_summary,
            dispatch=DispatchView(blocked=bool(reason or snapshot.dispatch.active_run_id), reason=reason,
                                  active_run_id=snapshot.dispatch.active_run_id, worker_running=worker_running),
            source=sources[kind], refresh_interval_s=self.settings.refresh_interval_s,
            stale_after_s=self.settings.stale_after_s,
        )

    def detail(self, kind: OrderType, order_id: str) -> OrderDetailView:
        """Sucht eine fachliche String-ID ausschließlich innerhalb ihres Auftragstyps."""
        item = self.repository.order_detail(kind, order_id)
        if item is None:
            raise LookupError("Der Auftrag ist nicht vorhanden.")
        stored, source = item
        return OrderDetailView(
            **self._view(stored, self._source(source), None).model_dump(),
            mes_auftrag=stored.order.payload,
            refresh_interval_s=self.settings.refresh_interval_s,
            stale_after_s=self.settings.stale_after_s,
        )
