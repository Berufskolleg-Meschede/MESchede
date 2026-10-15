"""Geordnete PLC-Zugriffe über die vorhandene OPC-UA-Implementierung."""

import asyncio
import logging
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Protocol

from app.clients.opc_ua_client import OpcUaClient
from app.domain.order_run import OrderType
from app.domain.plc_snapshot import PlcSnapshot, ProductObservation
from app.models.mes_auftrag import MESAuftrag
from app.models.order_input import CatalogProduct, OrderCatalog, CATALOG_BYTE_FIELDS, CATALOG_REAL_FIELDS


logger = logging.getLogger(__name__)


class PlcGateway(Protocol):
    """Definiert die tatsächliche Austauschgrenze für Liveclient und Tests."""

    async def read(self, kind: OrderType) -> PlcSnapshot:
        """Liest einen zugeordneten Auftragsslot."""
        ...

    async def read_input_catalog(self, kind: OrderType) -> OrderCatalog:
        """Liest Produktspezifikationen und vorhandene Queue-Slots ohne Steuerungsaktion."""
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

    def __init__(self, url: str, settings_provider=None) -> None:
        """Legt Verbindungen erst bei einer tatsächlichen Operation an."""
        self.url = url
        if settings_provider is None:
            from app.services.settings_service import get_current_settings

            settings_provider = get_current_settings
        self.settings_provider = settings_provider
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mes-plc")
        self.client: OpcUaClient | None = None
        self.connected = False
        self.roots: dict[OrderType, object] = {}
        self.root_names: tuple[str, str, str] | None = None
        self.database = None

    async def _invoke(self, operation):
        """Lässt eine begonnene I/O-Operation auch bei Taskcancel geordnet auslaufen."""
        future = asyncio.get_running_loop().run_in_executor(self.executor, operation)
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            await future
            raise

    def _root(self, kind: OrderType):
        """Löst konfigurierte Auftragsslots auf dem I/O-Thread auf."""
        configured = self.settings_provider()
        root_names = (
            configured.opcua_node_production_order,
            configured.opcua_node_delivery_order,
            "DB_MES_Schnittstelle",
        )
        if self.client is None:
            if not self.url:
                raise ValueError("Die OPC-UA-Adresse ist nicht konfiguriert.")
            self.client = OpcUaClient(self.url)
        if not self.roots or root_names != self.root_names:
            try:
                if not self.connected:
                    self.client.client.connect()
                    self.connected = True
                database = self.client._find_node_by_name_sync(
                    self.client.client.get_objects_node(), root_names[2], None,
                )
                if database is None:
                    raise KeyError(f"{root_names[2]} ist im OPC-UA-Server nicht vorhanden.")
                self.roots = {
                    OrderType.PRODUCTION: self.client._get_child(database, root_names[0]),
                    OrderType.DELIVERY: self.client._get_child(database, root_names[1]),
                }
                self.database = database
                self.root_names = root_names
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
        configured = self.settings_provider()
        header = self.client._get_child(root, configured.opcua_node_kopf)
        number = self.client._get_child(header, "Auftragsnummer").get_value()
        initial_status = self.client.read_status_mes(root, configured.opcua_node_feedback, configured.opcua_node_status)
        initial_command = self.client.read_auftragssteuerung(root, configured.opcua_node_kopf, configured.opcua_node_auftragssteuerung)
        content = self.client._get_child(root, configured.opcua_node_inhalt)
        count = self.client.read_anzahl(root, configured.opcua_node_inhalt)
        if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 255:
            raise ValueError("Die PLC liefert eine ungültige Produktanzahl.")
        products = []
        for index in range(count):
            item = self.client._get_product_queue_item(content, index, configured.opcua_node_produktqueue_pattern)
            products.append(ProductObservation(
                index, self._optional_value(item, "ProduktID"), self._optional_value(item, "Seriennummer"),
                self._optional_value(item, "Sequenznummer"), self._optional_value(item, "Status"),
                self._optional_value(item, "Fehlercode"),
            ))
        status = self.client.read_status_mes(root, configured.opcua_node_feedback, configured.opcua_node_status)
        command = self.client.read_auftragssteuerung(root, configured.opcua_node_kopf, configured.opcua_node_auftragssteuerung)
        final_count = self.client.read_anzahl(root, configured.opcua_node_inhalt)
        final_number = self.client._get_child(header, "Auftragsnummer").get_value()
        if (final_number, final_count, status, command) != (number, count, initial_status, initial_command):
            raise ValueError("Der PLC-Auftragszustand änderte sich während der Beobachtung.")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (number, status, command)):
            raise ValueError("Die PLC liefert ungültige Auftrags- oder Statuswerte.")
        return PlcSnapshot(kind, number, command, status, datetime.now(timezone.utc), tuple(products), count)

    async def read(self, kind: OrderType) -> PlcSnapshot:
        """Liest den Slot ohne Schreibzugriff auf MES-, HMI- oder Feedbackwerte."""
        return await self._invoke(lambda: self._read_sync(kind))

    def _read_input_catalog_sync(self, kind: OrderType) -> OrderCatalog:
        """Verlangt tatsächliche ID-/Textfelder und lückenlose Queue-Slots ab null."""
        root = self._root(kind)
        catalog = self.client._get_child(self.database, "Produktspezifikation")
        products = []
        for node in catalog.get_children():
            name = node.get_browse_name().Name
            index = name.rsplit("[", 1)[-1].rstrip("]")
            if not index.isdecimal() or int(index) == 0:
                continue
            fields = {field.get_browse_name().Name: field for field in node.get_children()}
            product_id = fields["ProduktID"].get_value()
            text = fields["Produkttext"].get_value()
            if product_id == 0 and text == "":
                continue
            specification = {}
            for field in CATALOG_BYTE_FIELDS:
                value = fields[field].get_value()
                if type(value) is not int or not 0 <= value <= 255:
                    raise ValueError(f"Das SPS-Bauplanfeld {field} ist kein gültiger USInt-Wert.")
                specification[field] = value
            for field in CATALOG_REAL_FIELDS:
                value = fields[field].get_value()
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                    raise ValueError(f"Das SPS-Bauplanfeld {field} ist kein endlicher Zahlenwert.")
                specification[field] = value
            products.append(CatalogProduct(product_id=product_id, product_text=text,
                                           source_index=int(index), specification=specification))
        if len({item.product_id for item in products}) != len(products):
            raise ValueError("Die Produktspezifikationen enthalten doppelte Produkt-IDs.")
        configured = self.settings_provider()
        content = self.client._get_child(root, configured.opcua_node_inhalt)
        pattern = configured.opcua_node_produktqueue_pattern
        container_name = pattern.split("[", 1)[0]
        children = content.get_children()
        container = next((node for node in children if node.get_browse_name().Name == container_name), None)
        names = {node.get_browse_name().Name for node in (container.get_children() if container else children)}
        capacity = 0
        while capacity < 255 and (str(capacity) in names or pattern.format(index=capacity) in names):
            capacity += 1
        return OrderCatalog(products=products, capacity=capacity, observed_at=datetime.now(timezone.utc))

    async def read_input_catalog(self, kind: OrderType) -> OrderCatalog:
        """Serialisiert die reine Katalog-/Kapazitätsabfrage mit dem vorhandenen PLC-I/O."""
        return await self._invoke(lambda: self._read_input_catalog_sync(kind))

    async def write(self, kind: OrderType, payload: MESAuftrag) -> None:
        """Nutzt den vorhandenen validierten Writer mit Start als letzter Operation."""
        def operation():
            """Schreibt den ausgewählten Auftrag ausschließlich im I/O-Thread."""
            root = self._root(kind)
            configured = self.settings_provider()
            self.client.write_order(
                root, payload, 1 if kind == OrderType.PRODUCTION else 4,
                configured.opcua_node_kopf, configured.opcua_node_inhalt,
                configured.opcua_node_auftragssteuerung, configured.opcua_node_produktqueue_pattern,
            )
        await self._invoke(operation)

    async def acknowledge(self, kind: OrderType, expected_order_number: int) -> None:
        """Löscht MES-Eingaben und Anzahl vor dem abschließenden Resetkommando."""
        def operation():
            """Quittiert den passenden Slot ohne Änderung an HMI oder Feedback."""
            root = self._root(kind)
            configured = self.settings_provider()
            header = self.client._get_child(root, configured.opcua_node_kopf)
            if self.client._get_child(header, "Auftragsnummer").get_value() != expected_order_number:
                raise ValueError("Die PLC-Auftragsidentität änderte sich vor dem Reset.")
            if (self.client.read_status_mes(root, configured.opcua_node_feedback, configured.opcua_node_status) != 5 or
                    self.client.read_auftragssteuerung(root, configured.opcua_node_kopf, configured.opcua_node_auftragssteuerung) != 1):
                raise ValueError("Der PLC-Abschluss ist vor dem Reset nicht mehr bestätigt.")
            self.client.clear_product_queue(root, configured.opcua_node_inhalt, configured.opcua_node_produktqueue_pattern)
            self.client.write_anzahl(root, 0, configured.opcua_node_inhalt)
            if self.client.read_anzahl(root, configured.opcua_node_inhalt) != 0:
                raise ValueError("Die PLC-Produktanzahl wurde beim Reset nicht auf null bestätigt.")
            self.client.write_auftragssteuerung(root, 0, configured.opcua_node_kopf, configured.opcua_node_auftragssteuerung)
        await self._invoke(operation)

    def _disconnect(self) -> None:
        """Beendet die Clientverbindung auf demselben I/O-Thread."""
        client, self.client = self.client, None
        self.connected = False
        self.roots = {}
        self.root_names = None
        self.database = None
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
