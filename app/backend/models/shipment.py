from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Enum, Field, SQLModel

from app.backend.models.database_enums import ShipmentStatus, ShipmentType


class ShipmentBase(SQLModel):
    order_id: int = Field(default=None, foreign_key="order.id")
    reference: str
    shipment_date: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
    )
    shipment_status: ShipmentStatus | None = Field(
        default=ShipmentStatus.scheduled, sa_column=Column(Enum(ShipmentStatus))
    )
    shipment_type: ShipmentType = Field(
        default=None, sa_column=Column(Enum(ShipmentType))
    )
    carrier_name: str
    shipping_method: str
    payment_type: str


class Shipment(ShipmentBase, table=True):
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
