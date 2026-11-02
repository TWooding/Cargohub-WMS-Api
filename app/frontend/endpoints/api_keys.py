import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, select

from app.backend.database import get_session
from app.backend.models import ApiKey, Role
from app.backend.services import api_key_service
from app.backend.services.audit_service import audit
from app.core.security import utcnow
from app.middleware.auth import CurrentPrincipal

# Permissie (api-keys:<method>) wordt afgedwongen door de default guard op de api_router.
router = APIRouter(prefix="/api-keys", tags=["api-keys"])
Db = Annotated[Session, Depends(get_session)]


class ApiKeyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=100)
    role_id: int
    client_id: int | None = None
    expires_in_days: int | None = Field(default=365, ge=1, le=3650)
    ip_allowlist: str | None = Field(default=None, max_length=500)  # "10.0.0.0/24,192.0.2.7"


def _view(k: ApiKey) -> dict:
    return {"id": k.id, "key_id": k.key_id, "label": k.label, "role": k.role.name, "client_id": k.client_id,
            "last_used_at": k.last_used_at, "expires_at": k.expires_at, "revoked_at": k.revoked_at}


@router.post("", status_code=status.HTTP_201_CREATED, summary="API key uitgeven")
def issue(body: ApiKeyIn, request: Request, db: Db, response: Response, p: CurrentPrincipal):
    """De key staat alleen in dit antwoord; daarna is alleen de hash nog bekend."""
    if p.kind != "user":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "API keys cannot issue API keys")
    role = db.get(Role, body.role_id)
    if not role:
        raise HTTPException(422, "unknown role_id")
    if role.name == "client" and body.client_id is None:
        raise HTTPException(422, "client_id is required for the client role")
    row, raw = api_key_service.generate(
        db, label=body.label, role=role, client_id=body.client_id, created_by=p.id,
        expires_in_days=body.expires_in_days, ip_allowlist=body.ip_allowlist)
    db.commit()
    audit(db, request, "api_key_issued", kind="user", pid=p.id, resource="api-keys", method="post",
          status=201, detail=f"key_id={row.key_id} label={row.label} role={role.name}")
    response.headers["Cache-Control"] = "no-store"
    return {**_view(row), "api_key": raw}


@router.get("", summary="API keys (zonder geheim)")
def list_keys(db: Db):
    return [_view(k) for k in db.exec(select(ApiKey).order_by(ApiKey.label))]


@router.delete("/{key_pk}", status_code=status.HTTP_204_NO_CONTENT, summary="API key intrekken")
def revoke(key_pk: uuid.UUID, request: Request, db: Db, p: CurrentPrincipal):
    row = db.get(ApiKey, key_pk)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "not found")
    if not row.revoked_at:
        row.revoked_at = utcnow()
        db.add(row)
        db.commit()
        audit(db, request, "api_key_revoked", kind="user", pid=p.id, resource="api-keys", method="delete",
              status=204, detail=f"key_id={row.key_id}")
    return Response(status_code=204)
