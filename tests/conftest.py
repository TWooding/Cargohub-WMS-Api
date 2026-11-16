import os

# Moet vóór het importeren van de app staan: Settings eist een JWT_SECRET.
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-0000")
os.environ.setdefault("COOKIE_SECURE", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from app.backend import models  # noqa: F401  (registers tables)
from app.backend.database import get_session
from app.backend.models import Role, User
from app.backend.services import api_key_service
from app.backend.services.auth_seed import seed
from app.main import app
from app.middleware.rate_limit import limiter


@pytest.fixture
def session():
    # In-memory SQLite so tests don't need the Postgres container.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed(session)
        yield session


@pytest.fixture(autouse=True)
def _reset_limiter():
    limiter.reset()


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    # Not used as a context manager, so the lifespan (Postgres init_db) is skipped.
    yield TestClient(app, base_url="https://testserver")
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(session):
    """Een API key met rol facility_management (alle rechten), voor tests die niet over auth gaan."""
    admin = User(username="fixture-admin", email="fixture@x.nl", password_hash="x",
                 role_id=session.exec(select(Role).where(Role.name == "facility_management")).one().id)
    session.add(admin)
    session.commit()
    role = session.exec(select(Role).where(Role.name == "facility_management")).one()
    _, raw = api_key_service.generate(session, label="tests", role=role, client_id=None, created_by=admin.id,
                                      expires_in_days=1, ip_allowlist=None)
    session.commit()
    return {"X-API-Key": raw}
