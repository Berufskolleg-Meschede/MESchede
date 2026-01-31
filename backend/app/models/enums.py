from enum import Enum

class MachineStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"