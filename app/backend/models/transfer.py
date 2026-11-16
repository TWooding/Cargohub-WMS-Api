from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Enum, Field, SQLModel

from app.backend.models.database_enums import TransferStatus


class TransferBase(SQLModel):
    from_location_id: int = Field(foreign_key="location.id")
    to_location_id: int = Field(foreign_key="location.id")
    reference: str
    transfer_status: TransferStatus | None = Field(
        default=TransferStatus.scheduled, sa_column=Column(Enum(TransferStatus))
    )


class Transfer(TransferBase, table=True):
    """Database table."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )
