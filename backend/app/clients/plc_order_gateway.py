"""Geordnete PLC-Zugriffe über die vorhandene OPC-UA-Implementierung."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Protocol

from app.clients.opc_ua_client import OpcUaClient
from app.domain.order_run import OrderType
from app.domain.plc_snapshot import PlcSnapshot, ProductObservation
from app.models.mes_auftrag import MESAuftrag


logger = logging.getLogger(__name__)


class PlcGateway(Protocol):
    """Definiert die tatsächliche Austauschgrenze für Liveclient und Tests."""

    async def read(self, kind: OrderType) -> PlcSnapshot:
        """Liest einen zugeordneten Auftragsslot."""
        ...

    async def write(self, kind: OrderType, payload: MESAuftrag) -> None:
        """Schreibt vorbereitete Eingabedaten und zuletzt den Startbefehl."""
        ...

    async def acknowledge(self, kind: OrderType, expected_order_number: int) -> None:
        """Quittiert einen bereits dauerhaft gesicherten Abschluss."""
        ...

    async def close(self) -> None:
        """Beendet die Verbindung erst nach bereits begonnenen Operationen."""
        ...


class PlcOrderGateway:
    """Serialisiert synchrone Clientoperationen in genau einem I/O-Thread."""

    def __init__(self, url: str) -> None:
        """Legt Verbindungen erst bei einer tatsächlichen Operation an."""
        self.url = url
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mes-plc")
        self.client: OpcUaClient | None = None
        self.roots: dict[OrderType, object] = {}

    async def _invoke(self, operation):
        """Lässt eine begonnene I/O-Operation auch bei Taskcancel geordnet auslaufen."""
        future = asyncio.get_running_loop().run_in_executor(self.executor, operation)
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            await future
            raise

    def _root(self, kind: OrderType):
        """Verbindet und löst beide bekannten Slotnamen auf dem I/O-Thread auf."""
        if self.client is None:
            if not self.url:
                raise ValueError("Die OPC-UA-Adresse ist nicht konfiguriert.")
            self.client = OpcUaClient(self.url)
            try:
                self.client.client.connect()
                database = self.client._find_node_by_name_sync(
                    self.client.client.get_objects_node(), "DB_MES_Schnittstelle", None,
                )
                if database is None:
                    raise KeyError("DB_MES_Schnittstelle ist im OPC-UA-Server nicht vorhanden.")
                self.roots = {
                    OrderType.PRODUCTION: self.client._get_child(database, "MESAuftragProduktion"),
                    OrderType.DELIVERY: self.client._get_child(database, "MESAuftragKommissionieren"),
                }
            except Exception:
                try:
                    self._disconnect()
                except Exception:
                    logger.warning("Die fehlgeschlagene OPC-UA-Verbindung konnte nicht getrennt werden.", exc_info=True)
                raise
        return self.roots[kind]

    def _optional_value(self, node, name: str) -> int | None:
        """Lässt nicht verfügbare Produktfelder unbekannt statt Standardwerte einzusetzen."""
        try:
            value = self.client._get_child(node, name).get_value()
        except KeyError:
            return None
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def _read_sync(self, kind: OrderType) -> PlcSnapshot:
        """Verhindert gemischte Produktresultate beim Wechsel der Auftragsnummer."""
        root = self._root(kind)
        header = self.client._get_child(root, "Kopf")
        number = self.client._get_child(header, "Auftragsnummer").get_value()
        initial_status = self.client.read_status_mes(root)
        initial_command = self.client.read_auftragssteuerung(root)
        content = self.client._get_child(root, "Inhalt")
        count = self.client._get_child(content, "Anzahl").get_value()
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 255:
            raise ValueError("Die PLC liefert eine ungültige Produktanzahl.")
        products = []
        for index in range(count):
            item = self.client._get_product_queue_item(content, index)
            products.append(ProductObservation(
                index, self._optional_value(item, "ProduktID"), self._optional_value(item, "Seriennummer"),
                self._optional_value(item, "Sequenznummer"), self._optional_value(item, "Status"),
                self._optional_value(item, "Fehlercode"),
            ))
        status = self.client.read_status_mes(root)
        command = self.client.read_auftragssteuerung(root)
        final_count = self.client.read_anzahl(root)
        final_number = self.client._get_child(header, "Auftragsnummer").get_value()
        if (final_number, final_count, status, command) != (number, count, initial_status, initial_command):
            raise ValueError("Der PLC-Auftragszustand änderte sich während der Beobachtung.")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (number, status, command)):
            raise ValueError("Die PLC liefert ungültige Auftrags- oder Statuswerte.")
        return PlcSnapshot(kind, number, command, status, datetime.now(timezone.utc), tuple(products), count)

    async def read(self, kind: OrderType) -> PlcSnapshot:
        """Liest den Slot ohne Schreibzugriff auf MES-, HMI- oder Feedbackwerte."""
        return await self._invoke(lambda: self._read_sync(kind))

    async def write(self, kind: OrderType, payload: MESAuftrag) -> None:
        """Nutzt den vorhandenen validierten Writer mit Start als letzter Operation."""
        def operation():
            """Schreibt den ausgewählten Auftrag ausschließlich im I/O-Thread."""
            root = self._root(kind)
            self.client.write_order(root, payload, 1 if kind == OrderType.PRODUCTION else 4)
        await self._invoke(operation)

    async def acknowledge(self, kind: OrderType, expected_order_number: int) -> None:
        """Löscht MES-Eingaben und Anzahl vor dem abschließenden Resetkommando."""
        def operation():
            """Quittiert den passenden Slot ohne Änderung an HMI oder Feedback."""
            root = self._root(kind)
            header = self.client._get_child(root, "Kopf")
            if self.client._get_child(header, "Auftragsnummer").get_value() != expected_order_number:
                raise ValueError("Die PLC-Auftragsidentität änderte sich vor dem Reset.")
            if self.client.read_status_mes(root) != 5 or self.client.read_auftragssteuerung(root) != 1:
                raise ValueError("Der PLC-Abschluss ist vor dem Reset nicht mehr bestätigt.")
            self.client.clear_product_queue(root)
            self.client.write_anzahl(root, 0)
            if self.client.read_anzahl(root) != 0:
                raise ValueError("Die PLC-Produktanzahl wurde beim Reset nicht auf null bestätigt.")
            self.client.write_auftragssteuerung(root, 0)
        await self._invoke(operation)

    def _disconnect(self) -> None:
        """Beendet die Clientverbindung auf demselben I/O-Thread."""
        client, self.client = self.client, None
        self.roots = {}
        if client is not None:
            client.client.disconnect()

    async def reconnect(self) -> None:
        """Verwirft eine fehlgeschlagene Verbindung vor dem nächsten Leseversuch."""
        await self._invoke(self._disconnect)

    async def close(self) -> None:
        """Entleert den I/O-Ausführungsweg vor dem Beenden des Executors."""
        try:
            await self._invoke(self._disconnect)
        finally:
            self.executor.shutdown(wait=True, cancel_futures=False)
