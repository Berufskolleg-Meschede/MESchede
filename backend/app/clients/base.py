from abc import ABC, abstractmethod
from typing import Any

class ProductionClient(ABC):

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def call_method(self, node_id: str, method: str, args: list[Any]) -> Any:
        pass