"""Geordneter Lesezugriff auf die SPS-Lagerknoten über die vorhandene OPC-UA-Implementierung."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.clients.opc_ua_client import OpcUaClient
from app.domain.lager_snapshot import GehaeuseBestand, LagerSnapshot, ProduktBestand


logger = logging.getLogger(__name__)


class PlcStorageGateway:
    """Serialisiert synchrone Lesezugriffe auf die Lagerknoten in genau einem I/O-Thread."""

    def __init__(self, url: str, settings_provider=None) -> None:
        """Legt die Verbindung erst bei einer tatsächlichen Operation an."""
        self.url = url
        if settings_provider is None:
            from app.services.settings_service import get_current_settings

            settings_provider = get_current_settings
        self.settings_provider = settings_provider
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mes-plc-storage")
        self.client: OpcUaClient | None = None
        self.connected = False
        self.database = None

    async def _invoke(self, operation):
        """Lässt eine begonnene I/O-Operation auch bei Taskcancel geordnet auslaufen."""
        future = asyncio.get_running_loop().run_in_executor(self.executor, operation)
        try:
            return await asyncio.shield(future)
        except asyncio.CancelledError:
            await future
            raise

    def _root(self):
        """Löst den Datenbaustein auf dem I/O-Thread auf und cached ihn bis zum Verbindungsabbruch."""
        if self.client is None:
            if not self.url:
                raise ValueError("Die OPC-UA-Adresse ist nicht konfiguriert.")
            self.client = OpcUaClient(self.url)
        if self.database is None:
            try:
                if not self.connected:
                    self.client.client.connect()
                    self.connected = True
                database = self.client._find_node_by_name_sync(
                    self.client.client.get_objects_node(), "DB_MES_Schnittstelle", None,
                )
                if database is None:
                    raise KeyError("DB_MES_Schnittstelle ist im OPC-UA-Server nicht vorhanden.")
                self.database = database
            except Exception:
                try:
                    self._disconnect()
                except Exception:
                    logger.warning("Die fehlgeschlagene OPC-UA-Verbindung konnte nicht getrennt werden.", exc_info=True)
                raise
        return self.database

    def _read_sync(self) -> LagerSnapshot:
        """Liest die vier Lagerknoten konsistent in einem Durchgang."""
        database = self._root()
        configured = self.settings_provider()

        gehaeuse_node = self.client._get_child(database, configured.opcua_node_lager_gehaeuse)
        gehaeuse_fields = self.client.read_fields(
            gehaeuse_node, ["StueckzahlGesamt", "StueckzahlRot", "StueckzahlSilber", "StueckzahlSchwarz"],
        )
        gehaeuse = GehaeuseBestand(
            gesamt=gehaeuse_fields["StueckzahlGesamt"],
            rot=gehaeuse_fields["StueckzahlRot"],
            silber=gehaeuse_fields["StueckzahlSilber"],
            schwarz=gehaeuse_fields["StueckzahlSchwarz"],
        )

        deckel_1_node = self.client._get_child(database, configured.opcua_node_magazin_deckel_1)
        deckel_blau = self.client._get_child(deckel_1_node, "Stueckzahl").get_value()

        deckel_2_node = self.client._get_child(database, configured.opcua_node_magazin_deckel_2)
        deckel_gruen = self.client._get_child(deckel_2_node, "Stueckzahl").get_value()

        produkte_node = self.client._get_child(database, configured.opcua_node_lager_produkte)
        produkte_fields = self.client.read_fields(produkte_node, [
            "StueckzahlGesamt", "StueckzahlSalzRot", "StueckzahlSalzSilber", "StueckzahlSalzSchwarz",
            "StueckzahlPfefferRot", "StueckzahlPfefferSilber", "StueckzahlPfefferSchwarz",
        ])
        produkte = ProduktBestand(
            gesamt=produkte_fields["StueckzahlGesamt"],
            salz_rot=produkte_fields["StueckzahlSalzRot"],
            salz_silber=produkte_fields["StueckzahlSalzSilber"],
            salz_schwarz=produkte_fields["StueckzahlSalzSchwarz"],
            pfeffer_rot=produkte_fields["StueckzahlPfefferRot"],
            pfeffer_silber=produkte_fields["StueckzahlPfefferSilber"],
            pfeffer_schwarz=produkte_fields["StueckzahlPfefferSchwarz"],
        )

        return LagerSnapshot(
            gehaeuse=gehaeuse,
            deckel_blau=deckel_blau,
            deckel_gruen=deckel_gruen,
            produkte=produkte,
            observed_at=datetime.now(timezone.utc),
        )

    async def read(self) -> LagerSnapshot:
        """Liest den aktuellen Lagerbestand ohne Schreibzugriff auf die SPS."""
        return await self._invoke(self._read_sync)

    def _disconnect(self) -> None:
        """Beendet die Clientverbindung auf demselben I/O-Thread."""
        client, self.client = self.client, None
        self.connected = False
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
