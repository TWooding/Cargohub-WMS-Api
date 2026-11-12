from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update
from sqlmodel import Session, select

from app.backend.database import get_session
from app.backend.models import AuthSession, RefreshToken, User
from app.backend.services import token_service
from app.backend.services.audit_service import audit
from app.core import passwords
from app.core.config import Settings, get_settings
from app.core.security import aware, client_ip, csrf_token, random_token, sha256, utcnow
from app.middleware.auth import (
    CSRF_COOKIE,
    SESSION_COOKIE,
    CurrentPrincipal,
    principal_from_api_key,
)
from app.middleware.rate_limit import enforce

# Geen permissie nodig: deze endpoints maken de identiteit juist aan (zie guard_check).
router = APIRouter(prefix="/auth", tags=["auth"])
Db = Annotated[Session, Depends(get_session)]
Cfg = Annotated[Settings, Depends(get_settings)]


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(max_length=150)
    password: str = Field(max_length=1024)
    mode: Literal["session", "token"] = "session"


class RefreshIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str = Field(max_length=1024)


class LogoutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    refresh_token: str | None = Field(default=None, max_length=1024)


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post("/login", summary="Inloggen met username + wachtwoord")
def login(body: LoginIn, request: Request, db: Db, settings: Cfg, response: Response):
    """`mode=session` (default) zet een HttpOnly-cookie (204); `mode=token` geeft een access+refresh token-paar."""
    ip = client_ip(request) or "?"
    username = body.username.strip().lower()
    # Rate limit vóór de (bewust trage) hash.
    enforce(f"login-ip:{ip}", settings.login_ip_limit, settings.rate_window_seconds)
    enforce(f"login-user:{username}", settings.login_user_limit, settings.rate_window_seconds)

    user = db.exec(select(User).where(User.username == username)).first()
    hash_ = user.password_hash if user else passwords.DUMMY_HASH  # altijd verifiëren
    if not passwords.verify(hash_, body.password) or not user:
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= settings.lockout_after:
                user.locked_until = utcnow() + timedelta(seconds=settings.lockout_seconds)
            db.add(user)
            db.commit()
        audit(db, request, "login_failed", kind="anonymous", pid=user.id if user else None,
              status=401, detail=f"username={username[:64]}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")  # één melding voor alle faalgevallen
    now = utcnow()
    if not user.is_active or (user.locked_until and aware(user.locked_until) > now):
        audit(db, request, "login_blocked", kind="user", pid=user.id, status=403)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "account unavailable")
    if passwords.needs_rehash(hash_):
        user.password_hash = passwords.hash_password(body.password)
    user.failed_attempts, user.locked_until = 0, None
    db.add(user)

    if body.mode == "token":
        pair = token_service.issue_token_pair(db, settings, user)
        db.commit()
        audit(db, request, "login_success", kind="user", pid=user.id, status=200, detail="mode=token")
        _no_store(response)
        return pair

    sid = random_token(32)
    db.add(AuthSession(
        id=sid, user_id=user.id, expires_at=now + timedelta(seconds=settings.session_ttl_seconds),
        ip=ip if ip != "?" else None, user_agent=(request.headers.get("user-agent") or "")[:255]))
    db.commit()
    audit(db, request, "login_success", kind="user", pid=user.id, status=204, detail="mode=session")
    resp = Response(status_code=204)
    resp.set_cookie(SESSION_COOKIE, sid, max_age=settings.session_ttl_seconds, httponly=True,
                    secure=settings.cookie_secure, samesite="lax", path="/")
    # Leesbaar voor JS (double-submit): de UI stuurt deze waarde terug in X-CSRF-Token.
    resp.set_cookie(CSRF_COOKIE, csrf_token(settings.jwt_secret, sid), max_age=settings.session_ttl_seconds,
                    httponly=False, secure=settings.cookie_secure, samesite="lax", path="/")
    return resp


@router.post("/refresh", summary="Refresh token inwisselen (rotatie)")
def refresh(body: RefreshIn, request: Request, db: Db, settings: Cfg, response: Response):
    enforce(f"refresh-ip:{client_ip(request)}", settings.refresh_ip_limit, settings.rate_window_seconds)
    now = utcnow()
    row = db.exec(select(RefreshToken).where(RefreshToken.token_hash == sha256(body.refresh_token))).first()
    if not row:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")

    def reuse():
        token_service.revoke_family(db, row.family_id)
        db.commit()
        audit(db, request, "refresh_reuse_detected", kind="user", pid=row.user_id, status=401)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")

    if row.used_at or row.revoked_at:
        reuse()
    if aware(row.expires_at) <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")
    # Atomair inwisselen: precies één gelijktijdige aanroep wint.
    claimed = db.execute(update(RefreshToken).where(
        RefreshToken.id == row.id, RefreshToken.used_at.is_(None), RefreshToken.revoked_at.is_(None)
    ).values(used_at=now)).rowcount
    if claimed != 1:
        db.rollback()
        reuse()
    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        token_service.revoke_family(db, row.family_id)
        db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid refresh token")
    pair = token_service.issue_token_pair(db, settings, user, family_id=row.family_id)
    db.commit()
    _no_store(response)
    return pair


@router.post("/token", summary="API key inwisselen voor een kort bearer token")
def exchange_api_key(request: Request, db: Db, settings: Cfg, response: Response,
                     x_api_key: Annotated[str | None, Header()] = None):
    """Optioneel voor apparaten: de key blijft in de kluis van het apparaat; zelfde permissiecheck."""
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    p = principal_from_api_key(request, db, settings, x_api_key)
    _no_store(response)
    return {"access_token": token_service.issue_access(settings, sub=p.id, role=p.role, knd="api_key"),
            "token_type": "bearer", "expires_in": settings.access_token_ttl_seconds}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Uitloggen")
def logout(request: Request, db: Db, p: CurrentPrincipal, body: LogoutIn | None = None):
    resp = Response(status_code=204)
    if p.via == "session":
        sid = request.cookies.get(SESSION_COOKIE)
        db.execute(update(AuthSession).where(AuthSession.id == sid).values(revoked_at=utcnow()))
        db.commit()
        resp.delete_cookie(SESSION_COOKIE, path="/")
        resp.delete_cookie(CSRF_COOKIE, path="/")
    elif p.via == "token" and p.kind == "user":
        raw = body.refresh_token if body else None
        row = db.exec(select(RefreshToken).where(RefreshToken.token_hash == sha256(raw))).first() if raw else None
        if not row or row.user_id != p.id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "refresh_token of this user required to log out a token session")
        token_service.revoke_family(db, row.family_id)
        db.commit()
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "API keys are revoked via DELETE /api-keys/{id}")
    audit(db, request, "logout", kind=p.kind, pid=p.id, status=204)
    return resp


@router.get("/me", summary="Huidige principal + permissielijst")
def me(p: CurrentPrincipal):
    return {"kind": p.kind, "id": p.id, "label": p.label, "role": p.role,
            "client_id": p.client_id, "permissions": sorted(p.permissions)}
