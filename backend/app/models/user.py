from sqlalchemy import Column, Integer, String, UUID

from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    email: str

class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)

class UserCreate(UserBase):
    pass

