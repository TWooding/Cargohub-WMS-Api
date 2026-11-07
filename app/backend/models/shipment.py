from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Enum, Field, SQLModel
from databaseEnums import ShipmentStatus, ShipmentType

class ShipmentBase(SQLModel):
    order_id: int = Field(default=None, foreign_key='Order.id')
    reference: str
    shipment_date: datetime = Field(nullable=False)
    shipment_status: Optional[ShipmentStatus] = Field(default=ShipmentStatus.scheduled, sa_column=Column(Enum(ShipmentStatus)))
    shipment_type: ShipmentType = Field(default=None, sa_column=Column(Enum(ShipmentType)))
    carrier_name: str
    shipping_method: str
    payment_type: str


class Shipment(ShipmentBase, table=True):
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
