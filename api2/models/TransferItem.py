from typing import Optional

from sqlmodel import Field, SQLModel

class TransferItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transfer_id: int = Field(foreign_key='Transfers.id')
    item_id: int = Field(foreign_key='Item.id')
    amount: int