from typing import Any

from opcua import Client
from .base import ProductionClient


class OpcUaClient(ProductionClient):
    def __init__(self, url: str) -> None:
        self.client = Client(url)

    async def connect(self):
        try:
            self.client.connect()
            print("Connected to OPC UA server")
        except Exception as e:
            print(f"Error connecting to OPC UA server: {e}")
            return False
        
    async def disconnect(self):
        try:
            self.client.disconnect()
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
        root = node or self.client.get_root_node()
        return self._find_node_by_name_sync(root, name, namespace_index)

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



    async def call_method(self, node_id: str, method: str, args: list[Any]) -> Any:
        pass
    