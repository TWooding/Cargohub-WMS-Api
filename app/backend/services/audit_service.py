import uuid

from fastapi import Request
from sqlmodel import Session

from app.backend.models import AuthEvent
from app.core.security import client_ip


def audit(
    session: Session,
    request: Request,
    event: str,
    *,
    kind: str | None = None,
    pid: uuid.UUID | None = None,
    resource: str | None = None,
    method: str | None = None,
    status: int | None = None,
    detail: str | None = None,
) -> None:
    """Schrijft direct en commit, zodat de regel blijft staan als de request daarna met een
    401/403 afbreekt. Geef nooit wachtwoorden, tokens of keys mee als detail."""
    rid = getattr(request.state, "request_id", None)
    session.add(
        AuthEvent(
            event=event,
            principal_kind=kind,
            principal_id=pid,
            resource=resource,
            method=method,
            status=status,
            ip=client_ip(request),
            request_id=uuid.UUID(rid) if rid else None,
            detail=detail[:200] if detail else None,
        )
    )
    session.commit()
