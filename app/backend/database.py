from collections.abc import Iterator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)


def init_db() -> None:
    # Import models so they register on SQLModel.metadata before create_all.
    from app.backend import models  # noqa: F401

    # Dev only: creates missing tables. Switch to Alembic migrations later.
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:  # users.username/email zijn citext
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    SQLModel.metadata.create_all(engine)
    from app.backend.services.auth_seed import bootstrap_admin, seed

    with Session(engine) as session:
        seed(session)
        bootstrap_admin(session, get_settings())


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    with Session(engine) as session:
        yield session
