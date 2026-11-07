from typing import Optional

from sqlmodel import Field, SQLModel

class OrderItemBase(SQLModel):
    order_id: int = Field(foreign_key='Order.id')
    item_id: int = Field(foreign_key='Item.id')
    amount: int
    unit_price: float


class OrderItem(OrderItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
