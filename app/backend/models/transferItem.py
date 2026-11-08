from typing import Optional

from sqlmodel import Field, SQLModel

class TransferItemBase(SQLModel):
    transfer_id: int = Field(foreign_key='transfer.id')
    item_id: int = Field(foreign_key='item.id')
    amount: int


class TransferItem(TransferItemBase, table=True):
    """Database table."""

    __tablename__ = 'transfer_item'

    id: Optional[int] = Field(default=None, primary_key=True)
