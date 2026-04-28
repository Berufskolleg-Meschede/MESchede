from typing import Optional

from sqlmodel import Field, Relationship

class StorageBase:
    quantity: int
    article_id: int

class Storage(StorageBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)
    article_id: int = Field(foreign_key="article.id")

    article: Optional["Article"] = Relationship(back_populates="storage")