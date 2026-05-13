"""Alembic env.py — supports both sync (Alembic CLI) and async (app runtime).

DATABASE_URL in .env uses 'postgresql+asyncpg://' for the app.
Alembic CLI needs a sync driver, so we swap the prefix automatically:
  postgresql+asyncpg://... → postgresql+psycopg2://...

No extra env var needed.
"""
import asyncio
import re
from logging.config import fileConfig

from alembic import context
# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine, pool
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base
import app.models  # noqa: F401 — register all models

# ── Derive sync URL from the async DATABASE_URL ──────────────────────────
# asyncpg  → psycopg2  (for Alembic CLI migrations)
ASYNC_URL: str = settings.DATABASE_URL
SYNC_URL: str = re.sub(
    r"^postgresql\+asyncpg://",
    "postgresql+psycopg2://",
    ASYNC_URL,
)

config = context.config

# Override alembic.ini placeholder with the real sync URL
config.set_main_option("sqlalchemy.url", SYNC_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ── Offline mode (generates SQL file, no live connection) ────────────────
def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (runs against live DB) ──────────────────────────────────
def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Use sync engine for Alembic CLI compatibility."""
    connectable = create_engine(SYNC_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        do_run_migrations(connection)
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
