import asyncio
from datetime import date, time as dt_time, datetime
from typing import Any

from opcua import Client, ua
from .base import ProductionClient
from ..models.mes_auftrag import MESAuftrag


class OpcUaClient(ProductionClient):
    _FIELD_NAME_MAP = {"Prioritaet": "Priorität"}

    def __init__(self, url: str) -> None:
        self.client = Client(url)

    async def connect(self):
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self.client.connect)
            print("Connected to OPC UA server")
        except Exception as e:
            print(f"Error connecting to OPC UA server: {e}")
            return False

    async def disconnect(self):
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, self.client.disconnect)
            print("Disconnected from OPC UA server")
        except Exception as e:
            print(f"Error disconnecting from OPC UA server: {e}")
            return False

    async def browse_nodes(self, node=None):
        if node is None:
            node = self.client.get_root_node()
        print(f"Node: {node.get_display_name().Text} | NodeId: {node.nodeid}")
        try:
            children = node.get_children()
            for child in children:
                print(child.get_display_name().Text)
                await self.browse_nodes(child)
        except Exception:
            pass  # Node might not have children

    async def find_node_by_name(
        self,
        name: str,
        namespace_index: int | None = None,
        node=None,
    ):
        loop = asyncio.get_running_loop()
        root = node or self.client.get_root_node()
        return await loop.run_in_executor(None, self._find_node_by_name_sync, root, name, namespace_index)

    def _find_node_by_name_sync(self, node, name: str, namespace_index: int | None):
        browse_name = node.get_browse_name()
        if namespace_index is not None:
            if browse_name.NamespaceIndex == namespace_index and browse_name.Name == name:
                return node
        else:
            if node.get_display_name().Text == name:
                return node

        for child in node.get_children():
            found = self._find_node_by_name_sync(child, name, namespace_index)
            if found:
                return found

        return None

    async def find_db_mes_schnittstelle(self, namespace_index: int | None = None):
        return await self.find_node_by_name("DB_MES_Schnittstelle", namespace_index)

    def _get_child(self, node, browse_name: str):
        for child in node.get_children():
            if child.get_browse_name().Name == browse_name:
                return child
        raise KeyError(f"OPC UA child node not found: {browse_name!r}")

    def read_auftragssteuerung(self, root_node) -> int:
        kopf = self._get_child(root_node, "Kopf")
        return self._get_child(kopf, "Auftragssteuerung").get_value()

    def _write_field(self, parent_node, browse_name: str, value) -> None:
        opc_name = self._FIELD_NAME_MAP.get(browse_name, browse_name)
        node = self._get_child(parent_node, opc_name)
        existing_vtype = node.get_data_value().Value.VariantType
        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime(value.year, value.month, value.day)
        elif isinstance(value, dt_time):
            value = datetime(1970, 1, 1, value.hour, value.minute, value.second)
        node.set_data_value(ua.DataValue(ua.Variant(value, existing_vtype)))

    def write_order(self, root_node, order: MESAuftrag, auftragsart: int) -> None:
        kopf_node = self._get_child(root_node, "Kopf")
        for field_name, value in order.kopf.model_dump().items():
            self._write_field(kopf_node, field_name, value)
        self._write_field(kopf_node, "AuftragsArt", auftragsart)
        self._write_field(kopf_node, "Anzahl", len(order.inhalt.Produktqueue))

        inhalt_node = self._get_child(root_node, "Inhalt")
        self._write_field(inhalt_node, "Anzahl", len(order.inhalt.Produktqueue))
        self._write_field(inhalt_node, "SeriennummerStart", order.inhalt.SeriennummerStart)

        for i, produkt in enumerate(order.inhalt.Produktqueue):
            item_node = self._get_child(inhalt_node, f"Produktqueue[{i}]")
            for field_name, value in produkt.model_dump().items():
                self._write_field(item_node, field_name, value)

        auftragssteuerung_node = self._get_child(kopf_node, "Auftragssteuerung")
        auftragssteuerung_node.set_data_value(
            ua.DataValue(ua.Variant(1, ua.VariantType.Byte))
        )

    async def call_method(self, node_id: str, method: str, args: list[Any]) -> Any:
        pass

    async def call_production_order(self, mes_production_order_node_id: str) -> None:
        pass
