from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, text
from sqlmodel import Enum, Field, SQLModel
from DatabaseEnums import ShipmentStatus, ShipmentType

class Shipment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(default=None, foreign_key='Order.id')
    reference: str
    shipment_date: datetime = Field(nullable=False)
    shipment_status: Optional[ShipmentStatus] = Field(default=ShipmentStatus.scheduled, sa_column=Column(Enum(ShipmentStatus)))
    shipment_type: ShipmentType = Field(default=None, sa_column=Column(Enum(ShipmentType)))
    carrier_name: str
    shipping_method: str
    payment_type: str
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
