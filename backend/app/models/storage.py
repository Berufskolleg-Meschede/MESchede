from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from .article import Article


class StorageBase(SQLModel):
    quantity: int
    article_id: int


class Storage(StorageBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)
    article_id: int = Field(foreign_key="article.id", unique=True)
    quantity: Optional[int] = Field(default=None, nullable=True)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    article: Optional[Article] = Relationship(back_populates="storage")


class StorageRead(SQLModel):
    id: Optional[int]
    article_id: int
    quantity: Optional[int]
    updated_at: Optional[datetime]
    article: Optional[Article] = None


class StorageEvent(SQLModel, table=True):
    event_id: str = Field(primary_key=True, max_length=128)
    article_id: int = Field(foreign_key="article.id")
    event_type: str = Field(max_length=16)
    occurred_at: datetime
    received_at: datetime = Field(default_factory=datetime.utcnow)
