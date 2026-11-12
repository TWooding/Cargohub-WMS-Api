import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.backend.database import get_session
from app.backend.models import AuthSession, Role, User
from app.backend.services import token_service
from app.backend.services.audit_service import audit
from app.core import passwords
from app.core.config import Settings, get_settings
from app.core.security import utcnow
from app.middleware.auth import CurrentPrincipal

# Permissies (users:*, roles:*) worden afgedwongen door de default guard op de api_router.
router = APIRouter(tags=["users"])
Db = Annotated[Session, Depends(get_session)]
EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=150)
    email: str = Field(max_length=254, pattern=EMAIL)
    password: str = Field(max_length=1024)
    role_id: int
    client_id: int | None = None


class UserUpdate(BaseModel):
    """Mass assignment: alleen deze velden; onbekende velden (bv. password_hash) geven 422."""

    model_config = ConfigDict(extra="forbid")
    email: str | None = Field(default=None, max_length=254, pattern=EMAIL)
    role_id: int | None = None
    client_id: int | None = None
    is_active: bool | None = None


def _view(u: User) -> dict:
    return {"id": u.id, "username": u.username, "email": u.email, "role": u.role.name,
            "role_id": u.role_id, "client_id": u.client_id, "is_active": u.is_active}


def _check_client(role: Role, client_id: int | None) -> None:
    if role.name == "client" and client_id is None:
        raise HTTPException(422, "client_id is required for the client role")


@router.get("/users", summary="Gebruikers")
def list_users(db: Db):
    return [_view(u) for u in db.exec(select(User).order_by(User.username))]


@router.get("/roles", summary="Rollen met permissies")
def list_roles(db: Db):
    return [{"id": r.id, "name": r.name, "description": r.description,
             "permissions": sorted(p.key for p in r.permissions)} for r in db.exec(select(Role))]


@router.post("/users", status_code=201, summary="Gebruiker aanmaken")
def create_user(body: UserCreate, request: Request, db: Db, p: CurrentPrincipal,
                settings: Annotated[Settings, Depends(get_settings)]):
    try:
        passwords.validate_new_password(body.password, settings.min_password_length)
    except ValueError as e:
        raise HTTPException(422, str(e))
    role = db.get(Role, body.role_id)
    if not role:
        raise HTTPException(422, "unknown role_id")
    _check_client(role, body.client_id)
    user = User(username=body.username.strip().lower(), email=body.email.strip().lower(),
                password_hash=passwords.hash_password(body.password), role_id=role.id, client_id=body.client_id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "username or email already exists")
    db.refresh(user)
    audit(db, request, "user_created", kind="user", pid=p.id, resource="users", method="post", status=201,
          detail=f"user={user.id} role={role.name}")
    return _view(user)


@router.put("/users/{user_id}", summary="Gebruiker bijwerken (rol, actief, e-mail)")
def update_user(user_id: uuid.UUID, body: UserUpdate, request: Request, db: Db, p: CurrentPrincipal):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "not found")
    fields = body.model_fields_set
    old_role = user.role.name
    if "role_id" in fields and body.role_id != user.role_id:
        if user.id == p.id:  # niemand wijzigt zijn eigen rol
            audit(db, request, "access_denied", kind=p.kind, pid=p.id, resource="users", method="put",
                  status=403, detail="self role change")
            raise HTTPException(403, "you cannot change your own role")
        role = db.get(Role, body.role_id)
        if not role:
            raise HTTPException(422, "unknown role_id")
        user.role_id, user.role = role.id, role
    _check_client(user.role, body.client_id if "client_id" in fields else user.client_id)
    if "client_id" in fields:
        user.client_id = body.client_id
    if "email" in fields and body.email:
        user.email = body.email.strip().lower()
    if "is_active" in fields and body.is_active is not None:
        if user.id == p.id and not body.is_active:
            raise HTTPException(403, "you cannot deactivate yourself")
        user.is_active = body.is_active
        if not body.is_active:  # direct alle toegang intrekken
            db.execute(update(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
                       .values(revoked_at=utcnow()))
            token_service.revoke_user_tokens(db, user.id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "email already exists")
    if user.role.name != old_role:
        audit(db, request, "role_changed", kind="user", pid=p.id, resource="users", method="put", status=200,
              detail=f"user={user.id} {old_role}->{user.role.name}")
    return _view(user)
