import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.backend import models  # noqa: F401  (registers tables)
from app.backend.database import get_session
from app.main import app

API_KEY = "dev-key"


@pytest.fixture
def session():
    # In-memory SQLite so tests don't need the Postgres container.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    # Not used as a context manager, so the lifespan (Postgres init_db) is skipped.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    return {"API_KEY": API_KEY}
