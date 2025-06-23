import os
import uuid
from typing import AsyncGenerator, List

from dotenv import load_dotenv
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

# Load variables from a local .env if present
load_dotenv()


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    repr_cols: List[str] = []  # subclasses may override

    def __repr__(self) -> str:  # noqa: DunderMethod
        cols = ", ".join(
            f"{name}={getattr(self, name)!r}"
            for name in self.repr_cols
            if hasattr(self, name)
        )
        return f"<{self.__class__.__name__} {cols}>"


# Ensure DATABASE_URL is provided via environment.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set.\n"
        "Add it to a .env file or export it in your shell."
    )


def _unique_stmt_name():  # noqa: D401
    """Return a globally unique name for asyncpg prepared statements.

    Using a UUID avoids DuplicatePreparedStatementError when PgBouncer
    re-uses a backend connection that already has statements with the
    default names.
    """
    return f"ps_{uuid.uuid4().hex}"


# Recreate engine with new URL -------------------------------------------
# Disable prepared statement caching for compatibility with pgbouncer (Supabase)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=1,  # Limit pool size to avoid connection conflicts
    max_overflow=0,  # No overflow connections
    connect_args={
        # AsyncPG: disable prepared statement caching entirely for PgBouncer
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
        # Ensure a unique name is generated for every prepared statement
        "prepared_statement_name_func": _unique_stmt_name,
        "command_timeout": 60,  # Add command timeout
        "server_settings": {
            "application_name": "ii_pipeline",
            "search_path": "public",
        },
    },
)

# Session factory producing `AsyncSession`
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        yield session


# Sync engine helper
from functools import lru_cache

from sqlalchemy import create_engine

# ---------------------------------------------------------------------------
# Helper for Alembic / synchronous contexts

# We need a *synchronous* driver (psycopg2), not asyncpg, for Alembic. Build
# a separate Engine lazily and cache it.


@lru_cache(maxsize=1)
def get_sync_engine() -> Engine:
    """Return a sync SQLAlchemy Engine using psycopg2.

    Converts the async URL (postgresql+asyncpg://) to a sync one
    (postgresql+psycopg2://). Works for Supabase and any Postgres DSN.
    """

    if DATABASE_URL.startswith("postgresql+asyncpg://"):
        sync_url = DATABASE_URL.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://", 1
        )
    else:
        sync_url = DATABASE_URL  # assume already sync-compatible

    return create_engine(sync_url, pool_pre_ping=True)
