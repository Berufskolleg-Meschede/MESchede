from typing import List, Optional

from sqlmodel import SQLModel, Field, Relationship

class ArticleBase(SQLModel):
    name: str
    description: str
    price: float

class Article(ArticleBase, table=True):
    id: int = Field(default=None, primary_key=True, nullable=False)

    production_orders: List["ProductionOrder"] = Relationship(back_populates="article")
    delivery_orders: List["DeliveryOrder"] = Relationship(back_populates="article")
    storage: Optional["Storage"] = Relationship(back_populates="article")
