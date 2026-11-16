from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Field, SQLModel


class ItemTypeBase(SQLModel):
    name: str
    description: str


class ItemType(ItemTypeBase, table=True):
    """Database table."""

    __tablename__ = "item_type"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
