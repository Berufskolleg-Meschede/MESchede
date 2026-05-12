from typing import Any

from opcua import Client
from backend.app.clients.base import ProductionClient


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
        except:
            pass # Node might not have children



    async def call_method(self, node_id: str, method: str, args: list[Any]) -> Any:
        pass