import ipaddress
import uuid
from datetime import timedelta

from sqlmodel import Session, select

from app.backend.models import ApiKey, Role
from app.core.security import aware, constant_time_eq, random_alnum, sha256, utcnow

ENVS = {"live", "test"}
_DUMMY = sha256("dummy")


def generate(
    session: Session,
    *,
    label: str,
    role: Role,
    client_id: int | None,
    created_by: uuid.UUID,
    expires_in_days: int | None,
    ip_allowlist: str | None,
    env: str = "live",
) -> tuple[ApiKey, str]:
    """Maakt een key aan; de plaintext wordt alleen hier teruggegeven en nergens bewaard."""
    key_id, secret = random_alnum(8), random_alnum(46)
    row = ApiKey(
        key_id=key_id,
        key_hash=sha256(secret),
        label=label,
        role_id=role.id,
        client_id=client_id,
        created_by=created_by,
        ip_allowlist=ip_allowlist,
        expires_at=utcnow() + timedelta(days=expires_in_days) if expires_in_days else None,
    )
    session.add(row)
    return row, f"wms_{env}_{key_id}_{secret}"


def parse(header: str) -> tuple[str, str] | None:
    """wms_<env>_<key_id>_<secret>; key_id en secret zijn alfanumeriek, dus split op '_' is eenduidig."""
    parts = header.split("_")
    if len(parts) != 4 or parts[0] != "wms" or parts[1] not in ENVS or not parts[2] or not parts[3]:
        return None
    return parts[2], parts[3]


def authenticate(session: Session, header: str, ip: str | None) -> ApiKey | None:
    parsed = parse(header)
    if not parsed:
        return None
    key_id, secret = parsed
    row = session.exec(select(ApiKey).where(ApiKey.key_id == key_id)).first()
    ok = constant_time_eq(sha256(secret), row.key_hash if row else _DUMMY)  # altijd vergelijken
    if not row or not ok or not usable(row, ip):
        return None
    return row


def usable(row: ApiKey, ip: str | None) -> bool:
    if row.revoked_at or (row.expires_at and aware(row.expires_at) <= utcnow()):
        return False
    if row.ip_allowlist:
        try:
            addr = ipaddress.ip_address(ip or "")
            nets = [ipaddress.ip_network(n.strip(), strict=False) for n in row.ip_allowlist.split(",") if n.strip()]
        except ValueError:
            return False
        return any(addr in n for n in nets)
    return True
