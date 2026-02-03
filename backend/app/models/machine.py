from sqlalchemy import Column, Integer, UUID, String, Enum as SAEnum

from .enums import MachineStatus
from ..db.base import Base

class Machine(Base):
    __tablename__ = "machines"
    id = Column(UUID, primary_key=True, index=True)
    name = Column(String)
    type = Column(String)
    status = Column(SAEnum(MachineStatus, name="machine_status"), default=MachineStatus.OFFLINE, nullable=False)

