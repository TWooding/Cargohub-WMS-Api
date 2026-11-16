from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, SQLModel


class ItemGroupBase(SQLModel):
    name: str
    description: str


class ItemGroup(ItemGroupBase, table=True):
    """Database table."""

    __tablename__ = "item_group"

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
