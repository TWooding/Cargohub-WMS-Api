from typing import Optional

from sqlmodel import Field, SQLModel

class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key='Order.id')
    item_id: int = Field(foreign_key='Item.id')
    amount: int
    unit_price: float