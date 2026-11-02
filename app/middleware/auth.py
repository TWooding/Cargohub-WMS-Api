"""Stap 2-3 van de request lifecycle (Auth System Design, sectie 06):
identify (cookie | bearer | X-API-Key -> Principal) en authorize (resource:method)."""
import hmac
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from app.backend.database import get_session
from app.backend.models import ApiKey, AuthSession, User
from app.backend.services import api_key_service, token_service
from app.backend.services.audit_service import audit
from app.backend.services.auth_seed import RESOURCE_ALIASES
from app.core.config import Settings, get_settings
from app.core.security import aware, client_ip, csrf_token, utcnow
from app.middleware.rate_limit import enforce

SESSION_COOKIE = "wms_session"
CSRF_COOKIE = "wms_csrf"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
TOUCH_INTERVAL = timedelta(seconds=60)


@dataclass(frozen=True)
class Principal:
    kind: str  # "user" | "api_key"
    id: uuid.UUID
    label: str  # username of key-label
    role: str
    permissions: frozenset[str]  # {"inventory:put", ...}
    client_id: int | None
    via: str  # "session" | "token" | "api_key"


def _unauth() -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated", headers={"WWW-Authenticate": "Bearer"})


def _perms(role) -> frozenset[str]:
    return frozenset(p.key for p in role.permissions)


def _user_principal(user: User, via: str) -> Principal:
    return Principal("user", user.id, user.username, user.role.name, _perms(user.role), user.client_id, via)


def _key_principal(row: ApiKey, via: str) -> Principal:
    return Principal("api_key", row.id, row.label, row.role.name, _perms(row.role), row.client_id, via)


def principal_from_session(request: Request, db: Session, settings: Settings, session_id: str) -> Principal:
    row = db.get(AuthSession, session_id)
    now = utcnow()
    if not row or row.revoked_at or aware(row.expires_at) <= now:
        raise _unauth()
    user = db.get(User, row.user_id)
    if not user or not user.is_active:
        raise _unauth()
    if request.method not in SAFE_METHODS:  # CSRF alleen bij cookies: double-submit, gebonden aan de sessie
        expected = csrf_token(settings.jwt_secret, session_id)
        header = request.headers.get(CSRF_HEADER, "")
        cookie = request.cookies.get(CSRF_COOKIE, "")
        if not (hmac.compare_digest(header, expected) and hmac.compare_digest(cookie, expected)):
            audit(db, request, "csrf_failed", kind="user", pid=user.id, method=request.method, status=403)
            raise HTTPException(status.HTTP_403_FORBIDDEN, "csrf token missing or invalid")
    if now - aware(row.last_seen_at) > TOUCH_INTERVAL:  # sliding expiry: 8 uur inactiviteit
        row.last_seen_at = now
        row.expires_at = now + timedelta(seconds=settings.session_ttl_seconds)
        db.add(row)
        db.commit()
    return _user_principal(user, "session")


def principal_from_token(request: Request, db: Session, settings: Settings, bearer: str) -> Principal:
    claims = token_service.decode_access(settings, bearer)
    if not claims:
        raise _unauth()
    try:
        sub = uuid.UUID(claims["sub"])
    except ValueError:
        raise _unauth()
    # Rol en permissies vers uit de database, niet uit het token.
    if claims["knd"] == "user":
        user = db.get(User, sub)
        if not user or not user.is_active:
            raise _unauth()
        return _user_principal(user, "token")
    if claims["knd"] == "api_key":
        row = db.get(ApiKey, sub)
        if not row or not api_key_service.usable(row, client_ip(request)):
            raise _unauth()
        return _key_principal(row, "token")
    raise _unauth()


def principal_from_api_key(request: Request, db: Session, settings: Settings, header: str) -> Principal:
    ip = client_ip(request) or "?"
    row = api_key_service.authenticate(db, header, ip)
    if not row:
        enforce(f"keyfail:{ip}", settings.api_key_fail_limit, settings.rate_window_seconds)
        parsed = api_key_service.parse(header)
        audit(db, request, "api_key_failed", kind="anonymous", status=401, detail=parsed[0] if parsed else None)
        raise _unauth()
    now = utcnow()
    if not row.last_used_at or now - aware(row.last_used_at) > TOUCH_INTERVAL:
        row.last_used_at = now
        db.add(row)
        db.commit()
    return _key_principal(row, "api_key")


def current_principal(
    request: Request,
    db: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    wms_session: Annotated[str | None, Cookie()] = None,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header()] = None,
    api_key_v1: Annotated[str | None, Header(alias="API_KEY")] = None,  # v1-headernaam blijft werken
) -> Principal:
    if wms_session:
        return principal_from_session(request, db, settings, wms_session)
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value:
            return principal_from_token(request, db, settings, value.strip())
        raise _unauth()
    if x_api_key or api_key_v1:
        return principal_from_api_key(request, db, settings, (x_api_key or api_key_v1))
    raise _unauth()


CurrentPrincipal = Annotated[Principal, Depends(current_principal)]


def _check(request: Request, db: Session, p: Principal, resource: str, method: str) -> Principal:
    if f"{resource}:{method}" not in p.permissions:
        audit(db, request, "access_denied", kind=p.kind, pid=p.id, resource=resource, method=method, status=403)
        raise HTTPException(status.HTTP_403_FORBIDDEN, "insufficient permissions")
    return p


def require(resource: str, method: str):
    """Dependency-factory voor een expliciete check: dependencies=[Depends(require("inventory", "put"))]."""
    needed_method = method.lower()

    def guard(
        request: Request, db: Annotated[Session, Depends(get_session)], p: CurrentPrincipal
    ) -> Principal:
        return _check(request, db, p, resource, needed_method)

    guard.permission = f"{resource}:{needed_method}"  # voor de fail-closed controle (guard_check)
    return guard


def require_route_permission(
    request: Request,
    db: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    p: CurrentPrincipal,
) -> Principal:
    """Default guard op de hele api_router (fail closed): resource = eerste padsegment na de prefix,
    method = HTTP-method. Een resource die niet in de matrix staat, geeft voor iedereen 403."""
    segment = request.url.path.removeprefix(settings.api_prefix).lstrip("/").split("/")[0]
    resource = RESOURCE_ALIASES.get(segment, segment)
    return _check(request, db, p, resource, request.method.lower())


require_route_permission.permission = "*route*"


def client_scope(p: Principal) -> int | None:
    """Object-level filter (stap 4): voor rol `client` het client_id waarop gefilterd moet worden, voor
    andere rollen None (geen filter). Een client zonder client_id krijgt 403 (fail closed)."""
    if p.role == "client":
        if p.client_id is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "client principal has no client_id")
        return p.client_id
    return None
