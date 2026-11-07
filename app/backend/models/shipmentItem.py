from typing import Optional

from sqlmodel import Field, SQLModel

class ShipmentItemBase(SQLModel):
    shipment_id: int = Field(foreign_key='Shipment.id')
    item_id: int = Field(foreign_key='Item.id')
    amount: int


class ShipmentItem(ShipmentItemBase, table=True):
    """Database table."""

    id: Optional[int] = Field(default=None, primary_key=True)