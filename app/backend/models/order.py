from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Enum, Field, SQLModel

from app.backend.models.databaseEnums import OrderStatus


class OrderBase(SQLModel):
    client_id: int = Field(foreign_key='client.id')
    warehouse_id: int = Field(foreign_key='warehouse.id')
    ship_to_client_id: int = Field(foreign_key='client.id')
    bill_to_client_id: int = Field(foreign_key='client.id')
    order_date: datetime = Field(nullable=False)
    request_date: datetime = Field(nullable=False)
    reference: str
    customer_po_number: str
    order_status: Optional[OrderStatus] = Field(default=OrderStatus.pending, sa_column=Column(Enum(OrderStatus)))
    shipping_notes: str


class Order(OrderBase, table=True):
    """Database table."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )