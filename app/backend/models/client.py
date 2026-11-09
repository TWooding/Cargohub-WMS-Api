from datetime import datetime
from typing import Optional

from sqlalchemy import Column, TIMESTAMP, func
from sqlmodel import Field, SQLModel


class ClientBase(SQLModel):
    name: str
    address: str
    city: str
    zip_code: str
    province: str
    country: str
    contact_name: str
    contact_phone: str
    contact_email: str


class Client(ClientBase, table=True):

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
