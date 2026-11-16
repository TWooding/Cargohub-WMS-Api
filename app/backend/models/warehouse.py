from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, func
from sqlmodel import Field, SQLModel


class WarehouseBase(SQLModel):
    code: str
    name: str
    address: str
    city: str
    zip_code: str
    province: str
    country: str
    contact_name: str
    contact_phone: str
    contact_email: str


class Warehouse(WarehouseBase, table=True):
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


class WarehouseCreate(WarehouseBase):
    """Request body for POST."""


class WarehouseUpdate(SQLModel):
    """Request body for PUT/PATCH: every field optional."""

    code: str | None = None
    name: str | None = None
    address: str | None = None
    city: str | None = None
    zip_code: str | None = None
    province: str | None = None
    country: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class WarehouseRead(WarehouseBase):
    """Response body."""

    id: int
    created_at: datetime
    updated_at: datetime
