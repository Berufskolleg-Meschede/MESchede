"""Lebenszyklus des einzigen gemeinsamen Produktions-/Lieferworkers."""

import asyncio
import logging

from opcua import ua
from app.clients.plc_order_gateway import PlcGateway
from app.domain.order_run import OrderConflict, OrderType
from app.repositories.order_repository import OrderRepository
from app.repositories.worker_leadership import WorkerLeadership
from app.services.order_dispatch_service import OrderDispatchService
from app.services.order_recovery_service import OrderRecoveryService
from app.settings import OrderSettings


logger = logging.getLogger(__name__)


class OrderWorkerHost:
    """Besitzt Hintergrundtask, Verbindungen und Diagnose; Fachregeln bleiben in Services."""

    def __init__(self, repository: OrderRepository, gateway: PlcGateway, settings: OrderSettings, leadership=None) -> None:
        """Setzt austauschbare Services zusammen, ohne beim Konstruktorstart die PLC zu kontaktieren."""
        self.repository = repository
        self.gateway = gateway
        self.settings = settings
        self.leadership = leadership or WorkerLeadership(repository.engine)
        self.dispatch = OrderDispatchService(repository, gateway, settings, self.leadership)
        self.recovery = OrderRecoveryService(repository)
        self.task: asyncio.Task | None = None
        self.phase = "stopped"
        self.last_error: str | None = None
        self.recovering = True

    @property
    def running(self) -> bool:
        """Kennzeichnet echte Task-Liveness statt nur einer gespeicherten Online-Annahme."""
        return self.task is not None and not self.task.done()

    async def start(self) -> None:
        """Initialisiert nach Migration die Persistenz und startet genau einen Task."""
        if self.running:
            return
        await asyncio.to_thread(self.repository.initialize)
        self.phase = "starting"
        self.task = asyncio.create_task(self._run(), name="mes-order-worker")
        self.task.add_done_callback(self._finished)

    def _finished(self, task: asyncio.Task) -> None:
        """Macht einen unbehandelten Taskausstieg sofort sichtbar."""
        if task.cancelled():
            self.phase = "stopped"
            return
        error = task.exception()
        if error is not None:
            self.phase = "failed"
            self.last_error = str(error)
            logger.error("Der Auftragsworker wurde unerwartet beendet.", exc_info=(type(error), error, error.__traceback__))

    async def _run(self) -> None:
        """Beobachtet beide Slots, bevor der gemeinsame Dispatch weitergeführt wird."""
        try:
            while True:
                self.phase = "waiting_for_leadership"
                if not await self.leadership.acquire():
                    await asyncio.sleep(self.settings.poll_interval_s)
                    continue
                await self.leadership.assert_owned()
                self.phase = "observing_plc"
                observations = await self._observe()
                if self.recovering:
                    await self._recover(observations)
                    self.recovering = False
                self.phase = "dispatching"
                try:
                    await self.dispatch.tick(observations)
                except (OrderConflict, ValueError, OSError, ua.UaError) as error:
                    await self._fail_active(error)
                self.phase = "waiting_for_poll"
                await asyncio.sleep(self.settings.poll_interval_s)
        finally:
            try:
                await self.gateway.close()
            finally:
                await self.leadership.close()

    async def _observe(self) -> dict:
        """Aktualisiert Quellen unabhängig und erhält deren letzten Erfolgszeitpunkt bei Fehlern."""
        observations = {}
        for kind in OrderType:
            try:
                observation = await self.gateway.read(kind)
                await asyncio.to_thread(self.repository.source_success, kind, observation.observed_at)
                observations[kind] = observation
            except (OSError, TimeoutError, KeyError, ValueError, ua.UaError) as error:
                self.last_error = str(error)
                await asyncio.to_thread(self.repository.source_failure, kind, str(error))
        if len(observations) != len(OrderType):
            await asyncio.to_thread(self.repository.block, "Die PLC-Verbindung ist nicht für beide Slots verfügbar.")
            reconnect = getattr(self.gateway, "reconnect", None)
            if reconnect is not None:
                try:
                    await reconnect()
                except (OSError, ua.UaError):
                    logger.warning("Die PLC-Verbindung konnte nicht sauber getrennt werden.")
        return observations

    async def _recover(self, observations: dict) -> None:
        """Gleicht die persistierte Reservierung vor einer weiteren Übergabe ab."""
        snapshot = await asyncio.to_thread(self.repository.snapshot)
        active = next((item for item in snapshot.orders if item.run.id == snapshot.dispatch.active_run_id), None)
        if active is not None:
            await asyncio.to_thread(self.recovery.reconcile, active, observations)

    async def _fail_active(self, error: Exception) -> None:
        """Sichert Ausführungsunsicherheit, statt einen Fehlerauftrag aus der Queue zu verlieren."""
        self.last_error = str(error)
        snapshot = await asyncio.to_thread(self.repository.snapshot)
        if snapshot.dispatch.active_run_id:
            await asyncio.to_thread(self.repository.require_review, snapshot.dispatch.active_run_id, str(error))
        else:
            await asyncio.to_thread(self.repository.block, str(error))
        logger.warning("Die Auftragsverarbeitung benötigt einen Abgleich: %s", error)

    async def stop(self) -> None:
        """Stoppt die Auswahl; ein laufender I/O-Aufruf wird vom Gateway vor Lockfreigabe beendet."""
        if self.task is None or self.task.done():
            return
        self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        finally:
            self.phase = "stopped"

    def diagnostics(self, kind: OrderType) -> dict:
        """Liefert Workerinformationen ohne Verbindung oder Schreiben zur PLC."""
        snapshot = self.repository.snapshot()
        orders = [item for item in snapshot.orders if item.order.order_type == kind.value]
        active = next((item for item in orders if item.run.id == snapshot.dispatch.active_run_id), None)
        completed = [item for item in orders if item.run.phase == "completed"]
        return {
            "worker_running": self.running, "worker_phase": self.phase,
            "queue_size": sum(item.run.phase == "queued" for item in orders),
            "current_order_id": active.order.order_id if active else None,
            "last_order_id": orders[-1].order.order_id if orders else None,
            "last_completed_order_id": completed[-1].order.order_id if completed else None,
            "last_error": self.last_error,
        }
