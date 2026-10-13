"""Gemeinsamer FIFO-Dispatch mit dauerhaftem Nachweis vor PLC-Nebeneffekten."""

import asyncio
from datetime import timezone

from app.clients.plc_order_gateway import PlcGateway
from app.domain.order_run import OrderType, RunPhase
from app.domain.plc_snapshot import PlcSnapshot
from app.models.mes_auftrag import MESAuftrag
from app.repositories.order_repository import OrderRepository, StoredOrder
from app.services.product_result_service import ProductResultService
from app.settings import OrderSettings


class OrderDispatchService:
    """Reserviert genau einen Anlagenlauf und sichert Ergebnisse vor dem Reset."""

    def __init__(self, repository: OrderRepository, gateway: PlcGateway, settings: OrderSettings, leadership) -> None:
        """Übernimmt Persistenz, PLC-Verbindung, geprüften Vertrag und Führungsnachweis."""
        self.repository = repository
        self.gateway = gateway
        self.settings = settings
        self.leadership = leadership
        self.results = ProductResultService(repository, settings)

    async def tick(self, observations: dict[OrderType, PlcSnapshot]) -> None:
        """Verarbeitet einen Beobachtungszyklus ohne parallele Auftragsvergabe."""
        snapshot = await asyncio.to_thread(self.repository.snapshot)
        active = next((item for item in snapshot.orders if item.run.id == snapshot.dispatch.active_run_id), None)
        if active is not None:
            await self._continue(active, observations)
            return
        reason = self._readiness_reason(observations)
        await asyncio.to_thread(self.repository.block, reason)
        if reason is not None:
            return
        reserved = await asyncio.to_thread(self.repository.reserve_next)
        if reserved is not None:
            await self._start(reserved)

    def _readiness_reason(self, observations: dict[OrderType, PlcSnapshot]) -> str | None:
        """Verlangt einen freigegebenen Vertrag und Bereitschaft beider Slots."""
        if not self.settings.contract_verified:
            return "Der PLC-Vertrag ist noch nicht bestätigt; neue Starts sind gesperrt."
        if len(observations) != len(OrderType):
            return "Die PLC-Bereitschaft ist nicht für beide Auftragsarten bekannt."
        if not all(snapshot.ready for snapshot in observations.values()):
            return "Die Anlage ist nicht für einen neuen Auftrag bereit."
        return None

    async def _start(self, stored: StoredOrder) -> None:
        """Prüft nach dem Restpuffer erneut und persistiert Startunsicherheit vor dem Schreiben."""
        await asyncio.sleep(self.settings.rest_buffer_s)
        observations = {kind: await self.gateway.read(kind) for kind in OrderType}
        reason = self._readiness_reason(observations)
        if reason is not None:
            await asyncio.to_thread(self.repository.require_review, stored.run.id, reason)
            return
        await self.leadership.assert_owned()
        await asyncio.to_thread(self.repository.transition, stored.run.id, RunPhase.START_PENDING)
        await self.gateway.write(OrderType(stored.order.order_type), MESAuftrag.model_validate(stored.order.payload))

    async def _continue(self, stored: StoredOrder, observations: dict[OrderType, PlcSnapshot]) -> None:
        """Gibt selbst einen manuell beendeten Lauf erst bei belegter Anlagenbereitschaft frei."""
        ready = len(observations) == len(OrderType) and all(item.ready for item in observations.values())
        phase = RunPhase(stored.run.phase)
        if not stored.run.review_required and ready and phase in {RunPhase.COMPLETED, RunPhase.INTERRUPTED}:
            await asyncio.to_thread(self.repository.release_completed, stored.run.id)
            return
        if not stored.run.review_required and ready and phase == RunPhase.AWAITING_RESET:
            await asyncio.to_thread(self.repository.transition, stored.run.id, RunPhase.COMPLETED)
            await asyncio.to_thread(self.repository.release_completed, stored.run.id)
            return
        if not stored.run.review_required and phase in {RunPhase.COMPLETED, RunPhase.INTERRUPTED}:
            await asyncio.to_thread(self.repository.block, "Der Lauf ist bewertet; die Anlage ist noch nicht bereit.")
        observation = observations.get(OrderType(stored.order.order_type))
        if observation is None:
            await asyncio.to_thread(self.repository.require_review, stored.run.id, "Die PLC-Rückmeldung ist nicht verfügbar.")
            return
        await asyncio.to_thread(self.results.observe, stored.run.id, observation)
        if stored.run.review_required:
            return
        if observation.status == 5:
            if not self.settings.contract_verified:
                await asyncio.to_thread(self.repository.require_review, stored.run.id, "Der PLC-Abschlussvertrag ist nicht geprüft.")
                return
            await self._acknowledge(stored, observation)
        elif phase == RunPhase.RUNNING and observation.ready:
            await asyncio.to_thread(self.repository.require_review, stored.run.id, "Der Lauf ging ohne Endnachweis auf Idle zurück.")
        else:
            await self._check_timeout(stored)

    async def _acknowledge(self, stored: StoredOrder, observation: PlcSnapshot) -> None:
        """Quittiert erst nach dem bereits committed Ergebnisnachweis."""
        if observation.command != 1:
            return
        if stored.run.phase not in {RunPhase.AWAITING_RESET.value, RunPhase.COMPLETED.value, RunPhase.INTERRUPTED.value}:
            await asyncio.to_thread(self.repository.transition, stored.run.id, RunPhase.AWAITING_RESET)
        await self.leadership.assert_owned()
        await self.gateway.acknowledge(OrderType(stored.order.order_type))

    async def _check_timeout(self, stored: StoredOrder) -> None:
        """Lässt einen Timeout nicht als Abschluss oder Anlass für einen Doppelstart gelten."""
        limits = {
            RunPhase.START_PENDING.value: self.settings.start_timeout_s,
            RunPhase.RUNNING.value: self.settings.completion_timeout_s,
            RunPhase.AWAITING_RESET.value: self.settings.reset_timeout_s,
        }
        limit = limits.get(stored.run.phase)
        elapsed = (self.repository.clock() - stored.run.phase_changed_at.replace(tzinfo=timezone.utc)).total_seconds()
        if limit is not None and elapsed >= limit:
            await asyncio.to_thread(self.repository.require_review, stored.run.id, "Die PLC-Bestätigung ist nicht rechtzeitig eingegangen.")
