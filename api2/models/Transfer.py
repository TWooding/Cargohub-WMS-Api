from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, text
from sqlmodel import Enum, Field, SQLModel
from DatabaseEnums import TransferStatus


class Transfer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    from_location_id: int = Field(foreign_key='Location.id')
    to_location_id: int = Field(foreign_key='Location.id')
    reference: str
    transfer_status: Optional[TransferStatus] = Field(default=TransferStatus.scheduled, sa_column=Column(Enum(TransferStatus)))
    created_at: Optional[datetime] = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ))
    updated_at: Optional[datetime] = Field(sa_column=Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    ))
