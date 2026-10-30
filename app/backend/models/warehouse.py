from datetime import datetime
from typing import Optional

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


class WarehouseCreate(WarehouseBase):
    """Request body for POST."""


class WarehouseUpdate(SQLModel):
    """Request body for PUT/PATCH: every field optional."""

    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class WarehouseRead(WarehouseBase):
    """Response body."""

    id: int
    created_at: datetime
    updated_at: datetime
