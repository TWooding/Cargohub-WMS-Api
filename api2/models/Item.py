from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, text
from sqlmodel import Enum, Field, SQLModel
from DatabaseEnums import OrderStatus

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_line_id: int = Field(foreign_key='ItemLine.id')
    item_group_id: int = Field(foreign_key='ItemGroup.id')
    item_type_id: int = Field(foreign_key='ItemType.id')
    supplier_id: int = Field(foreign_key='Supplier.id')
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
