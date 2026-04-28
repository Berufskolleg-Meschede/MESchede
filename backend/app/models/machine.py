from .enums import MachineStatus

from sqlmodel import SQLModel, Field

class MachineBase(SQLModel):
    name: str
    type: str
    status: MachineStatus = MachineStatus.OFFLINE

class Machine(MachineBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)

class MachineCreate(MachineBase):
    pass

