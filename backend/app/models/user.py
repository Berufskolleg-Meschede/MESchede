from sqlalchemy import Column, Integer, String, UUID
from ..db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
