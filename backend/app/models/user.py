from typing import Optional

from sqlmodel import SQLModel, Field

from .enums import UserRole


class UserBase(SQLModel):
    email: str
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class User(UserBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)
    hashed_password: Optional[str] = Field(default=None)


class UserCreate(UserBase):
    password: str

