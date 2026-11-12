"""Auth-tabellen uit sectie 07 van het Auth System Design.

Typen zijn portable: Postgres in productie (citext/inet), SQLite in tests.
Geheimen staan alleen als hash in de database.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import CITEXT, INET
from sqlmodel import Field, Relationship, SQLModel

CIText = String().with_variant(CITEXT(), "postgresql")
Inet = String(45).with_variant(INET(), "postgresql")
SmallPK = SmallInteger().with_variant(Integer, "sqlite")
BigPK = BigInteger().with_variant(Integer, "sqlite")
TS = DateTime(timezone=True)


def _ts(**kw):
    return Field(default=None, sa_type=TS, **kw)


def _created():
    return Field(default=None, sa_type=TS, sa_column_kwargs={"server_default": func.now()})


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"
    role_id: int = Field(foreign_key="roles.id", primary_key=True, sa_type=SmallInteger)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True, sa_type=SmallInteger)


class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("resource", "method"),)
    id: Optional[int] = Field(default=None, primary_key=True, sa_type=SmallPK)
    resource: str
    method: str  # get|post|put|delete

    @property
    def key(self) -> str:
        return f"{self.resource}:{self.method}"


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    id: Optional[int] = Field(default=None, primary_key=True, sa_type=SmallPK)
    name: str = Field(sa_type=String, unique=True)
    description: Optional[str] = None
    permissions: list[Permission] = Relationship(
        link_model=RolePermission, sa_relationship_kwargs={"lazy": "selectin"}
    )


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(sa_type=CIText, unique=True)
    email: str = Field(sa_type=CIText, unique=True)
    password_hash: str
    role_id: int = Field(foreign_key="roles.id", sa_type=SmallInteger)
    # TODO: foreign_key="client.id" zodra de Client-tabel (PR 28-DatabaseModels) in app/backend/models staat.
    client_id: Optional[int] = None
    is_active: bool = True
    failed_attempts: int = 0
    locked_until: Optional[datetime] = _ts()
    created_at: Optional[datetime] = _created()
    updated_at: Optional[datetime] = Field(
        default=None, sa_type=TS, sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
    role: Role = Relationship(sa_relationship_kwargs={"lazy": "joined"})


class AuthSession(SQLModel, table=True):
    __tablename__ = "sessions"
    id: str = Field(primary_key=True)  # random 32 bytes
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    created_at: Optional[datetime] = _created()
    last_seen_at: Optional[datetime] = _created()
    expires_at: datetime = Field(sa_type=TS)
    ip: Optional[str] = Field(default=None, sa_type=Inet)
    user_agent: Optional[str] = None
    revoked_at: Optional[datetime] = _ts()


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    token_hash: bytes = Field(unique=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    family_id: uuid.UUID = Field(index=True)  # rotatie
    used_at: Optional[datetime] = _ts()
    revoked_at: Optional[datetime] = _ts()
    expires_at: datetime = Field(sa_type=TS)


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    key_id: str = Field(unique=True)  # lookup, niet geheim
    key_hash: bytes
    label: str  # bv. "smart glass 04"
    role_id: int = Field(foreign_key="roles.id", sa_type=SmallInteger)
    client_id: Optional[int] = None  # TODO: foreign_key="client.id", zie User
    last_used_at: Optional[datetime] = _ts()
    expires_at: Optional[datetime] = _ts()
    revoked_at: Optional[datetime] = _ts()
    created_by: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    ip_allowlist: Optional[str] = None  # komma-gescheiden CIDR's, optioneel
    role: Role = Relationship(sa_relationship_kwargs={"lazy": "joined"})


class AuthEvent(SQLModel, table=True):
    """Append-only audit log. Nooit wachtwoorden, tokens of keys."""

    __tablename__ = "auth_events"
    id: Optional[int] = Field(default=None, primary_key=True, sa_type=BigPK)
    at: Optional[datetime] = _created()
    event: str
    principal_kind: Optional[str] = None
    principal_id: Optional[uuid.UUID] = None
    resource: Optional[str] = None
    method: Optional[str] = None
    status: Optional[int] = None
    ip: Optional[str] = Field(default=None, sa_type=Inet)
    request_id: Optional[uuid.UUID] = None
    detail: Optional[str] = None  # korte context, bv. geprobeerde username
