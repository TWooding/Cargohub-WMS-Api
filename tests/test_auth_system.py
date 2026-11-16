"""Auth System Design rev. A: sessies, tokens, API keys, permissiematrix, security-eisen.
Draait op SQLite in-memory (zie conftest); Postgres-typen vallen daar terug op String."""
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.backend.models import ApiKey, AuthEvent, AuthSession, RefreshToken, Role, User
from app.backend.services.auth_seed import MATRIX
from app.core import passwords
from app.core.config import get_settings
from app.core.security import utcnow
from app.main import app
from app.middleware.auth import Principal, client_scope
from app.middleware.guard_check import unguarded_routes
from fastapi import HTTPException

PW = "correct horse battery"
P = get_settings().api_prefix
A = f"{P}/auth"


class Env:
    """Dunne wrapper zodat de tests kort blijven."""

    def __init__(self, client, session, settings):
        self.client, self.session, self.settings, self.app = client, session, settings, app


@pytest.fixture
def env(client, session, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "login_user_limit", 50)
    monkeypatch.setattr(s, "login_ip_limit", 500)
    monkeypatch.setattr(s, "lockout_after", 5)
    return Env(client, session, s)


def make_user(env, role="facility_management", username=None, client_id=None, password=PW):
    username = username or f"{role}-{uuid.uuid4().hex[:6]}"
    r = env.session.exec(select(Role).where(Role.name == role)).one()
    u = User(username=username, email=f"{username}@x.nl", password_hash=passwords.hash_password(password),
             role_id=r.id, client_id=client_id)
    env.session.add(u)
    env.session.commit()
    return username, u.id


def login_session(env, username, password=PW):
    c = TestClient(app, base_url="https://testserver")
    r = c.post(f"{A}/login", json={"username": username, "password": password})
    assert r.status_code == 204, r.text
    c.headers["X-CSRF-Token"] = c.cookies["wms_csrf"]
    return c


def login_token(env, username, password=PW):
    r = env.client.post(f"{A}/login", json={"username": username, "password": password, "mode": "token"})
    assert r.status_code == 200, r.text
    return r.json()


def bearer(tok):
    return {"Authorization": f"Bearer {tok['access_token']}"}


def events(env, name):
    return list(env.session.exec(select(AuthEvent).where(AuthEvent.event == name)))


def role_id(env, name):
    return env.session.exec(select(Role.id).where(Role.name == name)).one()


def new_key(env, admin, role_name, client_id=None):
    r = admin.post(f"{P}/api-keys", json={"label": "dev 04", "role_id": role_id(env, role_name), "client_id": client_id})
    assert r.status_code == 201, r.text
    return r.json()


# ---------- seed / matrix ----------
def test_matrix_matches_design(env):
    admin = login_session(env, make_user(env)[0])
    roles = {r["name"]: set(r["permissions"]) for r in admin.get(f"{P}/roles").json()}
    assert roles["order_picker"] == {"items:get", "locations:get", "inventory:get", "inventory:put",
                                     "transfers:get", "transfers:put", "orders:get", "orders:put"}
    assert roles["client"] == {"items:get", "orders:get", "orders:post"}
    assert "orders:get" not in roles["smart_glass_reader"]
    assert roles["facility_management"] == {f"{r}:{m}" for r in MATRIX for m in ("get", "post", "put", "delete")}
    for name in set(roles) - {"facility_management"}:
        assert not any(p.split(":")[0] in ("users", "roles", "api-keys") for p in roles[name])
        assert not any(p.endswith(":delete") for p in roles[name])


def test_every_route_declares_a_permission():
    assert unguarded_routes(app, P) == []
    app.get(f"{P}/leak")(lambda: "x")
    try:
        assert any("/leak" in r for r in unguarded_routes(app, P))
    finally:
        app.router.routes.pop()


# ---------- login / sessie ----------
def test_login_sets_hardened_cookie_and_me_works(env):
    name, _ = make_user(env, "order_picker")
    r = env.client.post(f"{A}/login", json={"username": name.upper(), "password": PW})
    assert r.status_code == 204
    cookies = [c.lower() for c in r.headers.get_list("set-cookie")]
    session_cookie = next(c for c in cookies if c.startswith("wms_session"))
    assert "httponly" in session_cookie and "secure" in session_cookie and "samesite=lax" in session_cookie
    me = env.client.get(f"{A}/me").json()
    assert me["role"] == "order_picker" and "inventory:put" in me["permissions"] and "orders:post" not in me["permissions"]
    assert events(env, "login_success")


def test_unauthenticated_is_401(env):
    assert env.client.get(f"{A}/me").status_code == 401
    assert env.client.get(f"{P}/users").status_code == 401
    assert env.client.get(f"{P}/warehouses", headers={"API_KEY": "dev-key"}).status_code == 401


def test_wrong_password_and_unknown_user_look_identical(env):
    name, _ = make_user(env)
    a = env.client.post(f"{A}/login", json={"username": name, "password": "nope-nope-nope"})
    b = env.client.post(f"{A}/login", json={"username": "nobody", "password": "nope-nope-nope"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()
    assert len(events(env, "login_failed")) == 2


def test_unknown_user_still_runs_a_hash(env, monkeypatch):
    calls = []
    real = passwords.verify
    monkeypatch.setattr(passwords, "verify", lambda h, p: calls.append(h) or real(h, p))
    env.client.post(f"{A}/login", json={"username": "nobody", "password": "whatever-whatever"})
    assert calls == [passwords.DUMMY_HASH]


def test_lockout_after_repeated_failures(env):
    name, uid = make_user(env)
    for _ in range(env.settings.lockout_after):
        assert env.client.post(f"{A}/login", json={"username": name, "password": "bad-bad-bad-bad"}).status_code == 401
    assert env.client.post(f"{A}/login", json={"username": name, "password": PW}).status_code == 403
    env.session.get(User, uid).locked_until = utcnow() - timedelta(seconds=1)
    env.session.commit()
    assert env.client.post(f"{A}/login", json={"username": name, "password": PW}).status_code == 204


def test_inactive_user_cannot_login(env):
    name, uid = make_user(env)
    env.session.get(User, uid).is_active = False
    env.session.commit()
    assert env.client.post(f"{A}/login", json={"username": name, "password": PW}).status_code == 403


def test_rate_limit_returns_429_with_retry_after(env, monkeypatch):
    monkeypatch.setattr(env.settings, "login_user_limit", 3)
    for _ in range(3):
        env.client.post(f"{A}/login", json={"username": "x", "password": "bad-bad-bad-bad"})
    r = env.client.post(f"{A}/login", json={"username": "x", "password": "bad-bad-bad-bad"})
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0


def test_logout_revokes_session_server_side(env):
    c = login_session(env, make_user(env)[0])
    sid = c.cookies["wms_session"]
    assert c.post(f"{A}/logout").status_code == 204
    c.cookies.set("wms_session", sid)  # een gestolen cookie werkt na uitloggen niet meer
    assert c.get(f"{A}/me").status_code == 401


def test_expired_session_is_401(env):
    c = login_session(env, make_user(env)[0])
    env.session.exec(select(AuthSession)).first().expires_at = utcnow() - timedelta(seconds=1)
    env.session.commit()
    assert c.get(f"{A}/me").status_code == 401


def test_session_is_sliding(env):
    c = login_session(env, make_user(env)[0])
    s = env.session.exec(select(AuthSession)).first()
    s.last_seen_at, s.expires_at = utcnow() - timedelta(minutes=10), utcnow() + timedelta(minutes=1)
    env.session.commit()
    assert c.get(f"{A}/me").status_code == 200
    exp = env.session.exec(select(AuthSession)).first().expires_at
    assert exp.replace(tzinfo=None) > (utcnow() + timedelta(hours=7)).replace(tzinfo=None)


# ---------- CSRF ----------
def test_cookie_post_requires_csrf_token(env):
    admin = login_session(env, make_user(env)[0])
    del admin.headers["X-CSRF-Token"]
    assert admin.post(f"{P}/users", json={}).status_code == 403
    assert events(env, "csrf_failed")
    admin.headers["X-CSRF-Token"] = "forged"
    assert admin.post(f"{P}/users", json={}).status_code == 403


def test_bearer_needs_no_csrf(env):
    t = login_token(env, make_user(env)[0])
    assert env.client.post(f"{P}/users", json={}, headers=bearer(t)).status_code == 422  # voorbij auth en csrf


# ---------- tokens ----------
def test_token_login_and_bearer_access(env):
    t = login_token(env, make_user(env, "order_picker")[0])
    assert env.client.get(f"{A}/me", headers=bearer(t)).json()["role"] == "order_picker"
    assert env.client.get(f"{A}/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_refresh_rotates_and_reuse_kills_family(env):
    t1 = login_token(env, make_user(env)[0])
    t2 = env.client.post(f"{A}/refresh", json={"refresh_token": t1["refresh_token"]}).json()
    assert t2["refresh_token"] != t1["refresh_token"]
    # de dief speelt het oude token opnieuw af
    assert env.client.post(f"{A}/refresh", json={"refresh_token": t1["refresh_token"]}).status_code == 401
    assert events(env, "refresh_reuse_detected")
    # ... en de echte client is nu ook uitgelogd
    assert env.client.post(f"{A}/refresh", json={"refresh_token": t2["refresh_token"]}).status_code == 401


def test_refresh_expired_or_unknown_is_401(env):
    t = login_token(env, make_user(env)[0])
    env.session.exec(select(RefreshToken)).first().expires_at = utcnow() - timedelta(seconds=1)
    env.session.commit()
    assert env.client.post(f"{A}/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401
    assert env.client.post(f"{A}/refresh", json={"refresh_token": "nope"}).status_code == 401


def test_refresh_token_is_stored_hashed(env):
    t = login_token(env, make_user(env)[0])
    row = env.session.exec(select(RefreshToken)).first()
    assert t["refresh_token"].encode() not in row.token_hash and len(row.token_hash) == 32


def test_access_and_refresh_tokens_are_not_interchangeable(env):
    t = login_token(env, make_user(env)[0])
    assert env.client.post(f"{A}/refresh", json={"refresh_token": t["access_token"]}).status_code == 401
    assert env.client.get(f"{A}/me", headers={"Authorization": f"Bearer {t['refresh_token']}"}).status_code == 401


def test_token_permissions_come_fresh_from_db(env):
    admin = login_session(env, make_user(env)[0])
    name, uid = make_user(env)  # tweede admin
    t = login_token(env, name)
    assert admin.put(f"{P}/users/{uid}", json={"role_id": role_id(env, "order_picker")}).status_code == 200
    assert env.client.get(f"{P}/users", headers=bearer(t)).status_code == 403  # token zegt nog facility_management
    assert events(env, "role_changed")


def test_token_logout_revokes_family(env):
    t = login_token(env, make_user(env)[0])
    r = env.client.post(f"{A}/logout", headers=bearer(t), json={"refresh_token": t["refresh_token"]})
    assert r.status_code == 204
    assert env.client.post(f"{A}/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


def test_deactivating_user_revokes_everything(env):
    admin = login_session(env, make_user(env)[0])
    name, uid = make_user(env, "order_picker")
    t = login_token(env, name)
    assert admin.put(f"{P}/users/{uid}", json={"is_active": False}).status_code == 200
    assert env.client.get(f"{A}/me", headers=bearer(t)).status_code == 401
    assert env.client.post(f"{A}/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401


# ---------- API keys ----------
def test_api_key_lifecycle(env):
    admin = login_session(env, make_user(env)[0])
    key = new_key(env, admin, "smart_glass_reader")
    raw = key["api_key"]
    assert raw.startswith("wms_live_") and len(raw.split("_")[3]) == 46
    h = {"X-API-Key": raw}
    me = env.client.get(f"{A}/me", headers=h).json()
    assert me["kind"] == "api_key" and me["role"] == "smart_glass_reader" and me["label"] == "dev 04"
    assert env.client.get(f"{P}/users", headers=h).status_code == 403
    assert events(env, "access_denied")
    row = env.session.exec(select(ApiKey)).first()
    assert raw.encode() not in row.key_hash and row.last_used_at is not None
    assert admin.delete(f"{P}/api-keys/{key['id']}").status_code == 204
    assert env.client.get(f"{A}/me", headers=h).status_code == 401
    listing = admin.get(f"{P}/api-keys").json()
    assert [k["revoked_at"] is not None for k in listing] == [True] and "api_key" not in listing[0]


def test_v1_header_name_still_works(env):
    admin = login_session(env, make_user(env)[0])
    raw = new_key(env, admin, "order_picker")["api_key"]
    assert env.client.get(f"{A}/me", headers={"API_KEY": raw}).status_code == 200


def test_api_key_wrong_secret_and_garbage(env):
    admin = login_session(env, make_user(env)[0])
    raw = new_key(env, admin, "order_picker")["api_key"]
    bad = raw[:-1] + ("a" if raw[-1] != "a" else "b")
    for h in (bad, "garbage", "wms_live_x_y_z"):
        assert env.client.get(f"{A}/me", headers={"X-API-Key": h}).status_code == 401
    assert events(env, "api_key_failed")


def test_api_key_expiry_and_ip_allowlist(env):
    admin = login_session(env, make_user(env)[0])
    h = {"X-API-Key": new_key(env, admin, "order_picker")["api_key"]}
    row = env.session.exec(select(ApiKey)).first()
    row.ip_allowlist = "10.1.2.3"
    env.session.commit()
    assert env.client.get(f"{A}/me", headers=h).status_code == 401
    row.ip_allowlist, row.expires_at = None, utcnow() - timedelta(seconds=1)
    env.session.commit()
    assert env.client.get(f"{A}/me", headers=h).status_code == 401


def test_api_key_failures_are_rate_limited(env):
    h = {"X-API-Key": "wms_live_aaaaaaaa_bbbb"}
    for _ in range(env.settings.api_key_fail_limit):
        env.client.get(f"{A}/me", headers=h)
    assert env.client.get(f"{A}/me", headers=h).status_code == 429


def test_key_to_token_exchange(env):
    admin = login_session(env, make_user(env)[0])
    raw = new_key(env, admin, "smart_glass_reader")["api_key"]
    t = env.client.post(f"{A}/token", headers={"X-API-Key": raw}).json()
    me = env.client.get(f"{A}/me", headers=bearer(t)).json()
    assert me["kind"] == "api_key" and me["role"] == "smart_glass_reader"
    assert env.client.post(f"{A}/token").status_code == 401
    # na intrekken is ook het uitgegeven token direct dood
    assert admin.delete(f"{P}/api-keys/{me['id']}").status_code == 204
    assert env.client.get(f"{A}/me", headers=bearer(t)).status_code == 401


def test_only_admin_can_issue_keys_and_keys_cannot(env):
    t = login_token(env, make_user(env, "order_picker")[0])
    body = {"label": "x", "role_id": 1}
    assert env.client.post(f"{P}/api-keys", json=body, headers=bearer(t)).status_code == 403
    admin = login_session(env, make_user(env)[0])
    raw = new_key(env, admin, "facility_management")["api_key"]  # admin-key bestaat, maar mag geen keys uitgeven
    assert env.client.post(f"{P}/api-keys", json=body, headers={"X-API-Key": raw}).status_code == 403


def test_client_key_requires_client_id(env):
    admin = login_session(env, make_user(env)[0])
    rid = role_id(env, "client")
    assert admin.post(f"{P}/api-keys", json={"label": "erp", "role_id": rid}).status_code == 422
    r = admin.post(f"{P}/api-keys", json={"label": "erp", "role_id": rid, "client_id": 7})
    assert r.status_code == 201
    assert env.client.get(f"{A}/me", headers={"X-API-Key": r.json()["api_key"]}).json()["client_id"] == 7


def test_issued_key_never_in_audit(env):
    admin = login_session(env, make_user(env)[0])
    secret = new_key(env, admin, "order_picker")["api_key"].split("_")[3]
    dump = " ".join(str(e.model_dump()) for e in env.session.exec(select(AuthEvent)))
    assert secret not in dump and events(env, "api_key_issued")


# ---------- autorisatie / escalatie ----------
def test_default_guard_on_domain_routes(env):
    picker = login_token(env, make_user(env, "order_picker")[0])
    h = bearer(picker)
    assert env.client.put(f"{P}/transfers/1", headers=h).status_code == 501    # transfers:put -> voorbij de guard
    assert env.client.get(f"{P}/inventories", headers=h).status_code == 501    # /inventories -> inventory:get
    assert env.client.post(f"{P}/inventories", headers=h).status_code == 403   # inventory:post ontbreekt
    assert env.client.get(f"{P}/orders", headers=h).status_code == 501
    assert env.client.post(f"{P}/orders", headers=h).status_code == 403        # orders:post ontbreekt
    assert env.client.delete(f"{P}/items/1", headers=h).status_code == 403
    assert env.client.get(f"{P}/warehouses", headers=h).status_code == 403     # resource niet in matrix: fail closed
    assert env.client.put(f"{P}/transfers/1").status_code == 401


def test_user_cannot_change_own_role(env):
    name, uid = make_user(env)
    c = login_session(env, name)
    assert c.put(f"{P}/users/{uid}", json={"role_id": role_id(env, "order_picker")}).status_code == 403
    assert not events(env, "role_changed")


def test_mass_assignment_rejected(env):
    admin = login_session(env, make_user(env)[0])
    _, uid = make_user(env, "order_picker")
    assert admin.put(f"{P}/users/{uid}", json={"password_hash": "x"}).status_code == 422
    assert admin.put(f"{P}/users/{uid}", json={"id": str(uuid.uuid4())}).status_code == 422


def test_picker_cannot_manage_users(env):
    c = login_session(env, make_user(env, "order_picker")[0])
    assert c.get(f"{P}/users").status_code == 403
    assert c.put(f"{P}/users/{uuid.uuid4()}", json={"role_id": 1}).status_code == 403


def test_create_user_enforces_password_policy_and_hashes(env):
    admin = login_session(env, make_user(env)[0])
    body = {"username": "P.Dekker", "email": "p@x.nl", "password": "kort", "role_id": role_id(env, "order_picker")}
    assert admin.post(f"{P}/users", json=body).status_code == 422
    assert admin.post(f"{P}/users", json={**body, "password": PW}).status_code == 201
    assert admin.post(f"{P}/users", json={**body, "password": PW}).status_code == 409
    u = env.session.exec(select(User).where(User.username == "p.dekker")).one()
    assert u.password_hash.startswith("$argon2id$")
    assert env.client.post(f"{A}/login", json={"username": "p.dekker", "password": PW}).status_code == 204


def test_client_scope_fails_closed():
    def principal(role, cid):
        return Principal("user", uuid.uuid4(), "c", role, frozenset(), cid, "session")

    with pytest.raises(HTTPException) as e:
        client_scope(principal("client", None))
    assert e.value.status_code == 403
    assert client_scope(principal("client", 5)) == 5
    assert client_scope(principal("order_picker", None)) is None


def test_request_id_is_echoed_and_audited(env):
    rid = str(uuid.uuid4())
    env.client.post(f"{A}/login", json={"username": "x", "password": "bad-bad-bad-bad"}, headers={"X-Request-ID": rid})
    assert str(events(env, "login_failed")[0].request_id) == rid
    assert env.client.get(f"{A}/me").headers["x-request-id"]


def test_password_rehash_on_login(env, monkeypatch):
    name, uid = make_user(env)
    before = env.session.get(User, uid).password_hash
    monkeypatch.setattr(passwords, "needs_rehash", lambda h: True)
    env.client.post(f"{A}/login", json={"username": name, "password": PW})
    assert env.session.get(User, uid).password_hash != before
