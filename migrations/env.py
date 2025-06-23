from __future__ import annotations

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

from app.db import get_sync_engine
from app.models import Base  # Import metadata

# Alembic Config object, provides access to values in the .ini file.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
logger = logging.getLogger(__name__)


# Online/async run ---------------------------------------------------------


def run_migrations_offline() -> None:  # noqa: D401
    """Run migrations in 'offline' mode."""
    url = str(get_sync_engine().url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:  # noqa: D401
    """Run migrations in 'online' mode."""

    connectable = get_sync_engine()

    with connectable.connect() as connection:  # type: ignore[arg-type]
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True if connection.dialect.name == "sqlite" else False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
