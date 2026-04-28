from enum import Enum

class MachineStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"

class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ERROR = "error"
    COMPLETED = "completed"