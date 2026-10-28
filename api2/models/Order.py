from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, text
from sqlmodel import Enum, Field, SQLModel
from DatabaseEnums import OrderStatus

class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key='Client.id')
    warehouse_id: int = Field(foreign_key='Warehouse.id')
    ship_to_client_id: int = Field(foreign_key='Client.id')
    bill_to_client_id: int = Field(foreign_key='Client.id')
    order_date: datetime = Field(nullable=False)
    request_date: datetime = Field(nullable=False)
    reference: str
    customer_po_number: str
    order_status: Optional[OrderStatus] = Field(default=OrderStatus.pending, sa_column=Column(Enum(OrderStatus)))
    shipping_notes: str
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