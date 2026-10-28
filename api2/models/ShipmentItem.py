from typing import Optional

from sqlmodel import Field, SQLModel

class ShipmentItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    shipment_id: int = Field(foreign_key='Shipment.id')
    item_id: int = Field(foreign_key='Item.id')
    amount: int