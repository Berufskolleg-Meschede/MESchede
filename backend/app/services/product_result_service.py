"""Korrelation und idempotente Übernahme tatsächlich gelesener Produktresultate."""

from app.domain.order_run import OrderConflict, RunPhase
from app.domain.plc_snapshot import PlcSnapshot
from app.models.mes_order import MesOrderRecord
from app.repositories.order_repository import OrderRepository
from app.settings import OrderSettings


class ProductResultService:
    """Erfasst eindeutige Einheiten statt Mengen bei jedem Poll hochzuzählen."""

    def __init__(self, repository: OrderRepository, settings: OrderSettings) -> None:
        """Übernimmt Persistenz und explizit bestätigte Ergebniscodes."""
        self.repository = repository
        self.settings = settings

    def observe(self, run_id: str, snapshot: PlcSnapshot) -> None:
        """Speichert Identität, belegten Laufzustand und verfügbare finale Resultate atomar."""
        with self.repository.transaction() as session:
            self.repository.lock_state(session)
            run = self.repository.load_run(session, run_id)
            order = session.get(MesOrderRecord, run.order_ref)
            if order is None or order.order_type != snapshot.order_type.value or order.plc_order_number != snapshot.order_number:
                raise OrderConflict("Die PLC-Rückmeldung gehört nicht eindeutig zum reservierten Lauf.")
            if snapshot.status not in {0, 1, 5}:
                raise OrderConflict("Der PLC-Laufstatus ist nicht zugeordnet. Bitte den Lauf prüfen.")
            self._observe_phase(run, snapshot)
            if snapshot.status == 5 and self.settings.contract_verified and self.settings.product_results:
                self._observe_results(run, self.repository.load_units(session, run_id), snapshot)

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

    def _observe_results(self, run, units: list, snapshot: PlcSnapshot) -> None:
        """Übernimmt Endresultate nur bei passender geplanter Einheitenidentität."""
        observations = {item.index: item for item in snapshot.products}
        changed = False
        for unit in units:
            observation = observations.get(unit.queue_index)
            if observation is None:
                continue
            identity = (observation.product_id, observation.serial_number, observation.sequence_number)
            expected = (unit.product_id, unit.serial_number, unit.sequence_number)
            if identity != expected:
                raise OrderConflict("Eine PLC-Produkteinheit gehört nicht zur gespeicherten Planung.")
            result = self.settings.product_results.get(observation.raw_status)
            if unit.result is not None and result != unit.result:
                raise OrderConflict("Ein bereits belegtes Produktresultat widerspricht der neuen Rückmeldung.")
            values = (result, observation.raw_status, observation.error_code)
            if (unit.result, unit.raw_status, unit.error_code) != values:
                unit.result, unit.raw_status, unit.error_code = values
                changed = True
        if observations and not run.result_observed:
            run.result_observed = True
            changed = True
        if changed:
            run.version += 1
        self._check_manual_totals(run, units)

    def _check_manual_totals(self, run, units: list) -> None:
        """Erhält manuelle Bewertungen; spätere Widersprüche benötigen eine erneute Prüfung."""
        complete = all(unit.result is not None for unit in units)
        for result, manual in (("good", run.manual_good_quantity), ("failed", run.manual_error_quantity)):
            actual = sum(unit.result == result for unit in units)
            if manual is not None and (actual > manual or complete and actual != manual):
                raise OrderConflict("Neue PLC-Ergebnisse widersprechen der manuellen Mengenbewertung.")
