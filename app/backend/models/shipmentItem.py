from typing import Optional

from sqlmodel import Field, SQLModel

class ShipmentItemBase(SQLModel):
    item_id: int = Field(foreign_key='item.id')
    shipment_id: int = Field(foreign_key='shipment.id')
    amount: int


class ShipmentItem(ShipmentItemBase, table=True):
    """Database table."""

    __tablename__ = "shipment_item"

    id: Optional[int] = Field(default=None, primary_key=True)