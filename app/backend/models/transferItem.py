from typing import Optional

from sqlmodel import Field, SQLModel

class TransferItemBase(SQLModel):
    transfer_id: int = Field(foreign_key='Transfers.id')
    item_id: int = Field(foreign_key='Item.id')
    amount: int


class TransferItem(TransferItemBase, table=True):
    """Database table."""

    id: Optional[int] = Field(default=None, primary_key=True)
