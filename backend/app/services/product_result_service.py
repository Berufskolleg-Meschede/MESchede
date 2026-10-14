"""Korrelation und idempotente Übernahme tatsächlich gelesener Produktresultate."""

from app.domain.order_run import OrderConflict, RunPhase
from app.domain.plc_snapshot import PlcSnapshot
from app.models.mes_order import MesOrderRecord
from app.models.storage_outbox_event import StorageOutboxEvent
from app.repositories.order_repository import OrderRepository
from app.settings import OrderSettings


class ProductResultService:
    """Erfasst finale PLC-Ergebnisse je Einheit statt Polls als Mengen zu zählen."""

    def __init__(self, repository: OrderRepository, settings: OrderSettings) -> None:
        """Übernimmt Persistenz und die bestätigte Zuordnung bekannter Ergebniscodes."""
        self.repository = repository
        self.settings = settings

    def observe(self, run_id: str, snapshot: PlcSnapshot) -> bool:
        """Speichert Identität, belegten Laufzustand und verfügbare finale Resultate atomar."""
        with self.repository.transaction() as session:
            state = self.repository.lock_state(session)
            run = self.repository.load_run(session, run_id)
            order = session.get(MesOrderRecord, run.order_ref)
            if order is None or order.order_type != snapshot.order_type.value or order.plc_order_number != snapshot.order_number:
                raise OrderConflict("Die PLC-Rückmeldung gehört nicht eindeutig zum reservierten Lauf.")
            if snapshot.status not in {0, 1, 5}:
                raise OrderConflict("Der PLC-Laufstatus ist nicht zugeordnet. Bitte den Lauf prüfen.")
            self._observe_phase(run, snapshot)
            if snapshot.status == 5:
                manual_conflict = self._observe_results(
                    run, state, self.repository.load_units(session, run_id), snapshot, order.order_type
                )
                if run.review_required and not manual_conflict:
                    run.review_required = False
                    run.review_reason = None
                    run.phase = RunPhase.COMPLETION_OBSERVED.value
                    run.phase_changed_at = self.repository.clock()
                    run.version += 1
                    state.blocked_reason = "Ein Lauf muss geprüft werden." if self.repository._has_reviews(session) else None
            elif snapshot.status == 0 and run.ended_at is not None and run.review_required:
                # The PLC has already returned to idle after a recorded completion.
                # Treat a stale review flag as resolved; the successful end status is
                # the project's completion criterion, and the control bit is reset.
                run.review_required = False
                run.review_reason = None
                run.phase = RunPhase.COMPLETED.value
                run.phase_changed_at = self.repository.clock()
                run.version += 1
                state.blocked_reason = "Ein Lauf muss geprüft werden." if self.repository._has_reviews(session) else None
            return not run.review_required

    def _observe_phase(self, run, snapshot: PlcSnapshot) -> None:
        """Beobachtet Start und Ende, ohne eine offene Operatorprüfung zu übergehen."""
        if run.last_observed_status != snapshot.status:
            run.last_observed_status = snapshot.status
            run.version += 1
        if snapshot.status == 1 and run.started_at is None:
            run.started_at = snapshot.observed_at
        if snapshot.status == 5 and run.ended_at is None:
            run.ended_at = snapshot.observed_at
        if run.review_required:
            return
        if snapshot.status == 1 and run.phase == RunPhase.START_PENDING.value:
            self.repository.change_phase(run, RunPhase.RUNNING)
        if snapshot.status == 5 and run.phase in {RunPhase.START_PENDING.value, RunPhase.RUNNING.value}:
            self.repository.change_phase(run, RunPhase.COMPLETION_OBSERVED)

    def _observe_results(self, run, state, units: list, snapshot: PlcSnapshot, order_type: str) -> bool:
        """Übernimmt Endresultate; bestätigter Abschluss setzt unbekannte Einheiten auf erfolgreich."""
        observations = {}
        ambiguous_indices = set()
        for item in snapshot.products:
            if item.index < 0 or item.index >= len(units):
                continue
            if item.index in observations:
                ambiguous_indices.add(item.index)
            else:
                observations[item.index] = item
        for index in ambiguous_indices:
            observations.pop(index, None)
        changed = False
        assumed = False
        newly_good_units = []
        for unit in units:
            observation = observations.get(unit.queue_index)
            if observation is not None:
                identity = (observation.product_id, observation.serial_number, observation.sequence_number)
                expected = (unit.product_id, unit.serial_number, unit.sequence_number)
                if identity != expected:
                    observation = None
            result = self.settings.product_results.get(observation.raw_status) if observation is not None else None
            if result is None:
                if unit.result is None:
                    result = "good"
                    assumed = True
                    raw_status = observation.raw_status if observation is not None else None
                    error_code = observation.error_code if observation is not None else None
                else:
                    result, raw_status, error_code = unit.result, unit.raw_status, unit.error_code
            else:
                raw_status, error_code = observation.raw_status, observation.error_code
            if unit.result is not None and result != unit.result:
                raise OrderConflict("Ein bereits belegtes Produktresultat widerspricht der neuen Rückmeldung.")
            previous_result = unit.result
            values = (result, raw_status, error_code)
            if (unit.result, unit.raw_status, unit.error_code) != values:
                unit.result, unit.raw_status, unit.error_code = values
                changed = True
            if previous_result is None and result == "good":
                newly_good_units.append(unit)

        self._check_manual_totals(run, state, units)
        manual_conflict = (
            run.review_required
            and run.review_reason == "Neue PLC-Ergebnisse widersprechen der manuellen Mengenbewertung."
        )
        if not manual_conflict:
            quantity_delta = 1 if order_type == "production" else -1
            for unit in newly_good_units:
                session.add(StorageOutboxEvent(
                    event_id=f"mes-order:{run.id}:{unit.queue_index}",
                    product_id=unit.product_id,
                    quantity_delta=quantity_delta,
                ))
        if units and not run.result_observed:
            run.result_observed = True
            changed = True
        if assumed and not run.completion_assumed:
            run.completion_assumed = True
            changed = True
        if changed:
            run.version += 1
        return manual_conflict

    def _check_manual_totals(self, run, state, units: list) -> None:
        """Erhält manuelle Bewertungen; spätere Widersprüche benötigen eine erneute Prüfung."""
        complete = all(unit.result is not None for unit in units)
        for result, manual in (("good", run.manual_good_quantity), ("failed", run.manual_error_quantity)):
            actual = sum(unit.result == result for unit in units)
            if manual is not None and (actual > manual or complete and actual != manual):
                self.repository.mark_review(run, state, "Neue PLC-Ergebnisse widersprechen der manuellen Mengenbewertung.")
                return
