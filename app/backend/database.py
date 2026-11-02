from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)


def init_db() -> None:
    # Import models so they register on SQLModel.metadata before create_all.
    from app.backend import models  # noqa: F401

    # Dev only: creates missing tables. Switch to Alembic migrations later.
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one database session per request."""
    with Session(engine) as session:
        yield session
