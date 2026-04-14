from enum import Enum


class MachineStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeliveryOrderType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ProductUnit(str, Enum):
    PIECE = "piece"
    KILOGRAM = "kilogram"
    LITER = "liter"
    METER = "meter"