from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

import app.database.base  # noqa: F401 — registers models with SQLModel metadata
from app.config.settings import settings

engine = create_engine(settings.database_url)


def create_db_and_tables() -> None:
    """Create all database tables on startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency that provides a database session per request."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
