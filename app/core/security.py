"""Kleine crypto/tijd-helpers zonder framework-afhankelijkheden."""
import hashlib
import hmac
import secrets
import string
from datetime import datetime, timezone

_ALNUM = string.ascii_letters + string.digits


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def aware(dt: datetime | None) -> datetime | None:
    """SQLite geeft naive datetimes terug; behandel die als UTC."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def random_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def random_alnum(n: int) -> str:
    return "".join(secrets.choice(_ALNUM) for _ in range(n))


def sha256(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


def constant_time_eq(a: bytes | str, b: bytes | str) -> bool:
    return hmac.compare_digest(a, b)


def csrf_token(secret: str, session_id: str) -> str:
    """Double-submit token, gebonden aan de sessie zodat een aanvaller het niet kan zetten."""
    return hmac.new(secret.encode(), b"csrf:" + session_id.encode(), hashlib.sha256).hexdigest()


def client_ip(request) -> str | None:
    # X-Forwarded-For wordt niet zelf vertrouwd: uvicorn (--proxy-headers) zet request.client
    # alleen vanaf vertrouwde proxies (--forwarded-allow-ips).
    return request.client.host if request.client else None
