from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, SQLModel


class InventoryBase(SQLModel):
    item_id: int = Field(foreign_key="item.id", primary_key=True)
    location_id: int = Field(foreign_key="location.id", primary_key=True)
    quantity_on_hand: int
    quantity_expected: int
    quantity_allocated: int


class Inventory(InventoryBase, table=True):
    """Database table."""

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
