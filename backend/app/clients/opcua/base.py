from abc import ABC, abstractmethod
from typing import Any


class ProductionClient(ABC):
    @abstractmethod
    def get_status(self) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def post_order(self, order: Any) -> Any:
        raise NotImplementedError
    
    @abstractmethod
    def get_order_status(self, order_id: Any) -> Any:
        raise NotImplementedError
    
    