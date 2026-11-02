"""Permissiematrix uit sectie 08. Elke cel = één rij in role_permissions."""
from sqlmodel import Session, select

from app.backend.models import Permission, Role, RolePermission, User
from app.core import passwords
from app.core.config import Settings

G, P, U, D = "get", "post", "put", "delete"
CRUD = (G, P, U, D)

ROLES = {
    "facility_management": "Beheer. Alles op alles, inclusief users, rollen en API keys.",
    "client": "Externe klant. Maakt orders aan en volgt ze; ziet uitsluitend eigen data.",
    "receiving_station": "Inbound. Ontvangt goederen, maakt transfers aan, boekt voorraad in.",
    "shipping": "Outbound. Werkt voorraad en orderstatus bij tijdens verzenden.",
    "order_picker": "Pickt items, werkt voorraad, transfers en orders bij. Alleen GET en PUT.",
    "smart_glass_reader": "Apparaat-rol op een API key. Leest en werkt voorraad bij, voert transfers uit.",
}

# Resources uit het ontwerp. Router-prefixen die hier anders heten, staan in RESOURCE_ALIASES.
MATRIX: dict[str, dict[str, tuple[str, ...]]] = {
    "items": {"facility_management": CRUD, "client": (G,), "receiving_station": (G,), "shipping": (G,),
              "order_picker": (G,), "smart_glass_reader": (G,)},
    "locations": {"facility_management": CRUD, "receiving_station": (G,), "shipping": (G,),
                  "order_picker": (G,), "smart_glass_reader": (G,)},
    "inventory": {"facility_management": CRUD, "receiving_station": (G, P, U), "shipping": (G, U),
                  "order_picker": (G, U), "smart_glass_reader": (G, U)},
    "transfers": {"facility_management": CRUD, "receiving_station": (G, P, U), "shipping": (G,),
                  "order_picker": (G, U), "smart_glass_reader": (G, U)},
    # client: POST/GET alleen op eigen records (client_scope in de endpoints)
    "orders": {"facility_management": CRUD, "client": (G, P), "receiving_station": (G, U),
               "shipping": (G, U), "order_picker": (G, U)},
    "users": {"facility_management": CRUD},
    "roles": {"facility_management": CRUD},
    "api-keys": {"facility_management": CRUD},
}

# Resources die het ontwerp niet noemt maar die in v2 wel bestaan: voorlopig alleen facility_management
# (fail closed). Rechten voor andere rollen toevoegen is één regel hier.
EXTRA_FM_ONLY = ["warehouses", "clients", "suppliers", "shipments", "item_lines", "item_groups", "item_types"]
for _r in EXTRA_FM_ONLY:
    MATRIX[_r] = {"facility_management": CRUD}

# v2 gebruikt /inventories, het ontwerp /inventory.
RESOURCE_ALIASES = {"inventories": "inventory"}


def seed(session: Session) -> None:
    """Idempotent: voegt ontbrekende rollen, permissies en koppelingen toe, verwijdert niets."""
    roles = {r.name: r for r in session.exec(select(Role))}
    for name, desc in ROLES.items():
        if name not in roles:
            roles[name] = Role(name=name, description=desc)
            session.add(roles[name])
    perms = {(p.resource, p.method): p for p in session.exec(select(Permission))}
    for resource in MATRIX:
        for method in CRUD:
            if (resource, method) not in perms:
                perms[(resource, method)] = Permission(resource=resource, method=method)
                session.add(perms[(resource, method)])
    session.flush()
    have = {(rp.role_id, rp.permission_id) for rp in session.exec(select(RolePermission))}
    for resource, per_role in MATRIX.items():
        for role_name, methods in per_role.items():
            for m in methods:
                pair = (roles[role_name].id, perms[(resource, m)].id)
                if pair not in have:
                    session.add(RolePermission(role_id=pair[0], permission_id=pair[1]))
    session.commit()


def bootstrap_admin(session: Session, settings: Settings) -> None:
    """Maakt de eerste facility_management-user aan uit de BOOTSTRAP_ADMIN_* variabelen, alleen als er geen users zijn."""
    if not settings.bootstrap_admin_username or session.exec(select(User)).first():
        return
    role = session.exec(select(Role).where(Role.name == "facility_management")).one()
    passwords.validate_new_password(settings.bootstrap_admin_password, settings.min_password_length)
    session.add(User(
        username=settings.bootstrap_admin_username.lower(),
        email=(settings.bootstrap_admin_email or f"{settings.bootstrap_admin_username}@localhost").lower(),
        password_hash=passwords.hash_password(settings.bootstrap_admin_password),
        role_id=role.id,
    ))
    session.commit()
