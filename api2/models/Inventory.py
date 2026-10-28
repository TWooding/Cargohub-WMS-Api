from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, text
from sqlmodel import Field, SQLModel

class Inventory(SQLModel, table=True):
    item_id: int = Field(foreign_key='Inventory.id', primary_key=True)
    location_id: int = Field(foreign_key='Location.id', primary_key=True)
    quantity_on_hand: int
    quantity_expected: int
    quantity_allocated: int
    created_at: Optional[datetime] = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    updated_at: Optional[datetime] = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    ))
