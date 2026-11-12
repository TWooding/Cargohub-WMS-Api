"""Beheer-CLI:  python -m app.cli seed | create-user"""
import argparse
import getpass
import sys

from sqlmodel import Session, select

from app.backend.database import engine, init_db
from app.backend.models import Role, User
from app.backend.services.auth_seed import seed
from app.core import passwords
from app.core.config import get_settings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("seed", help="tabellen + rollen + permissiematrix laden")
    cu = sub.add_parser("create-user")
    cu.add_argument("--username", required=True)
    cu.add_argument("--email", required=True)
    cu.add_argument("--role", default="facility_management")
    cu.add_argument("--client-id", type=int)
    args = ap.parse_args(argv)

    init_db()
    if args.cmd == "seed":
        return 0
    settings = get_settings()
    with Session(engine) as db:
        seed(db)
        role = db.exec(select(Role).where(Role.name == args.role)).first()
        if not role:
            print(f"onbekende rol {args.role!r}", file=sys.stderr)
            return 1
        password = getpass.getpass("Wachtwoord: ")
        try:
            passwords.validate_new_password(password, settings.min_password_length)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        db.add(User(username=args.username.lower(), email=args.email.lower(), role_id=role.id,
                    client_id=args.client_id, password_hash=passwords.hash_password(password)))
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
