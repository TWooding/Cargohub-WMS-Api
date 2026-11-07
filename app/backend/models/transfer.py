from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Enum, Field, SQLModel
from databaseEnums import TransferStatus


class TransferBase(SQLModel):
    from_location_id: int = Field(foreign_key='Location.id')
    to_location_id: int = Field(foreign_key='Location.id')
    reference: str
    transfer_status: Optional[TransferStatus] = Field(default=TransferStatus.scheduled, sa_column=Column(Enum(TransferStatus)))


class Transfer(TransferBase, table=True):
    """Database table."""

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
        ),
    )
