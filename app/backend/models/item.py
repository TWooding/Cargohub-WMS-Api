from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    item_line_id: int = Field(foreign_key="item_line.id")
    item_group_id: int = Field(foreign_key="item_group.id")
    item_type_id: int = Field(foreign_key="item_type.id")
    supplier_id: int = Field(foreign_key="supplier.id")
    item_code: str
    code: str
    description: str
    barcode: str
    model_number: str
    commodity_code: str
    unit_weight: float
    min_purchase_quantity: int
    case_size: int
    order_multiple: int
    packaging_type: str
    supplier_sku: str


class Item(ItemBase, table=True):
    """Database table."""

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
