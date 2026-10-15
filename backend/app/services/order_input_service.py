"""Lesende Erfassungsvorbereitung und Validierung vor erstmaliger Auftragsannahme."""

import asyncio
import logging
from datetime import datetime, timezone
from pytz import timezone as plant_timezone

from opcua import ua

from app.domain.order_run import OrderType
from app.models.order_dto import OrderPayload
from app.models.order_input import OrderCatalog, OrderInputContext, OrderInputError
from app.repositories.order_repository import OrderRepository
from app.repositories.product_catalog_repository import ProductCatalogRepository
from app.settings import OrderSettings


logger = logging.getLogger(__name__)


class OrderInputService:
    """Trennt SPS-Synchronisation vom rein datenbankgestützten Formular-/Annahmeweg."""

    def __init__(self, repository: OrderRepository, gateway, settings: OrderSettings, clock=None) -> None:
        """Übernimmt Persistenz, lesenden Gateway und austauschbare Anlagenzeit."""
        self.repository = repository
        self.gateway = gateway
        self.settings = settings
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.catalog_repository = ProductCatalogRepository(repository.engine)
        self.lock = asyncio.Lock()

    async def synchronize(self, kind: OrderType) -> OrderCatalog:
        """Liest ausschließlich den SPS-Katalog und übernimmt erst den vollständigen Snapshot."""
        async with self.lock:
            try:
                snapshot = await self.gateway.read_input_catalog(kind)
                if not self._fresh(snapshot):
                    raise ValueError("Die Produktdaten sind nicht aktuell verifiziert.")
                await asyncio.to_thread(self.catalog_repository.save, kind, snapshot)
            except (OSError, TimeoutError, KeyError, ValueError, ua.UaError):
                await asyncio.to_thread(self.catalog_repository.failed, kind,
                                        "Der SPS-Produktkatalog konnte nicht vollständig abgeglichen werden.")
                reconnect = getattr(self.gateway, "reconnect", None)
                if reconnect is not None:
                    try:
                        await reconnect()
                    except (OSError, ua.UaError):
                        logger.warning("Die Katalogverbindung konnte nicht getrennt werden.", exc_info=True)
                raise
            return snapshot

    async def catalog(self, kind: OrderType) -> OrderCatalog:
        """Validiert den gespeicherten Katalog, ohne eine SPS-Verbindung aufzubauen."""
        snapshot, error = await asyncio.to_thread(self.catalog_repository.read, kind)
        if error or snapshot is None:
            raise ValueError(error or "Der SPS-Produktkatalog ist noch unbekannt.")
        if not self._fresh(snapshot):
            raise ValueError("Der gespeicherte Produktkatalog ist veraltet. Bitte erneut abgleichen.")
        return snapshot

    def _fresh(self, snapshot: OrderCatalog) -> bool:
        """Akzeptiert keine veralteten oder in die Zukunft datierten Voraussetzungen."""
        age = (self.clock() - snapshot.observed_at).total_seconds()
        return 0 <= age < self.settings.catalog_stale_after_s

    async def prepare(self, kind: OrderType, worker_running: bool) -> OrderInputContext:
        """Liefert lokale Anlagenzeit, Vorschläge und einen expliziten Quellenzustand."""
        identifier, number = await asyncio.to_thread(self.repository.suggest_identifiers, kind)
        local = self.clock().astimezone(plant_timezone(self.settings.plant_timezone))
        snapshot, source_error = await asyncio.to_thread(self.catalog_repository.read, kind)
        error = None
        try:
            snapshot = await self.catalog(kind)
        except (OSError, TimeoutError, KeyError, ValueError, ua.UaError) as failure:
            logger.warning("Erfassungsvoraussetzungen nicht verfügbar: %s", failure)
            error = source_error or "Produktkatalog oder Queue-Kapazität nicht aktuell. Bitte die Produktdaten abgleichen."
        if not worker_running:
            error = "Der Auftragsworker ist nicht gestartet. Bitte den Backendstatus prüfen."
        if number is None:
            error = "Alle PLC-Auftragsnummern sind bereits vergeben. Bitte die Auftragsverwaltung prüfen."
        return OrderInputContext(
            available=error is None, suggested_order_id=identifier, suggested_plc_order_number=number,
            start_date=local.date(), start_time=local.time().replace(tzinfo=None, microsecond=0),
            plant_timezone=self.settings.plant_timezone,
            products=snapshot.products if snapshot else [], capacity=snapshot.capacity if snapshot else None,
            observed_at=snapshot.observed_at if snapshot else None, error=error,
            refresh_interval_s=self.settings.refresh_interval_s, stale_after_s=self.settings.catalog_stale_after_s,
        )

    def validate(self, payload: OrderPayload, snapshot: OrderCatalog) -> None:
        """Prüft den bestätigten Inhalt ohne Katalogtexte oder Werte still zu ersetzen."""
        if not self._fresh(snapshot):
            raise OrderInputError(("mes_auftrag", "inhalt", "Produktqueue"),
                                  "Die Produktdaten sind veraltet. Bitte erneut laden und prüfen.")
        queue = payload.mes_auftrag.inhalt.Produktqueue
        if len(queue) > snapshot.capacity:
            raise OrderInputError(("mes_auftrag", "inhalt", "Produktqueue"),
                                  f"Die Gesamtmenge darf höchstens {snapshot.capacity} Stück betragen.")
        if payload.mes_auftrag.inhalt.SeriennummerStart + len(queue) - 1 > 65535:
            raise OrderInputError(("mes_auftrag", "inhalt", "SeriennummerStart"),
                                  "Der Seriennummernbereich überschreitet 65535. Bitte die Startnummer oder Menge ändern.")
        products = {item.product_id: item.product_text for item in snapshot.products}
        for index, item in enumerate(queue):
            if products.get(item.ProduktID) != item.Produkttext:
                raise OrderInputError(("mes_auftrag", "inhalt", "Produktqueue", index, "ProduktID"),
                                      "Das Produkt ist nicht mehr mit diesen Daten verfügbar. Bitte erneut auswählen.")
