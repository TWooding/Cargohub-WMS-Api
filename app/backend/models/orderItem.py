from typing import Optional

from sqlmodel import Field, SQLModel

class OrderItemBase(SQLModel):
    order_id: int = Field(foreign_key='order.id')
    item_id: int = Field(foreign_key='item.id')
    amount: int
    unit_price: float


class OrderItem(OrderItemBase, table=True):
    __tablename__ = 'order_item'

    id: Optional[int] = Field(default=None, primary_key=True)
