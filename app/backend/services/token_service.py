import uuid
from datetime import timedelta

import jwt
from sqlalchemy import update
from sqlmodel import Session

from app.backend.models import RefreshToken, User
from app.core.config import Settings
from app.core.security import random_token, sha256, utcnow

ALG = "HS256"


def issue_access(settings: Settings, *, sub: uuid.UUID, role: str, knd: str) -> str:
    now = utcnow()
    return jwt.encode(
        {
            "sub": str(sub),
            "role": role,  # momentopname; permissies worden vers uit de database gelezen
            "typ": "access",
            "knd": knd,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(seconds=settings.access_token_ttl_seconds),
        },
        settings.jwt_secret,
        algorithm=ALG,
    )


def decode_access(settings: Settings, token: str) -> dict | None:
    try:
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=[ALG], options={"require": ["exp", "sub", "typ", "knd"]}
        )
    except jwt.PyJWTError:
        return None
    return claims if claims["typ"] == "access" else None


def issue_token_pair(session: Session, settings: Settings, user: User, family_id: uuid.UUID | None = None) -> dict:
    raw = random_token(48)  # opaque string, geen jwt
    session.add(
        RefreshToken(
            token_hash=sha256(raw),
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            expires_at=utcnow() + timedelta(seconds=settings.refresh_token_ttl_seconds),
        )
    )
    return {
        "access_token": issue_access(settings, sub=user.id, role=user.role.name, knd="user"),
        "refresh_token": raw,
        "token_type": "bearer",
        "expires_in": settings.access_token_ttl_seconds,
    }


def revoke_family(session: Session, family_id: uuid.UUID) -> None:
    session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )


def revoke_user_tokens(session: Session, user_id: uuid.UUID) -> None:
    session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
