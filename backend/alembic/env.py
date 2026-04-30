from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Convert the async DATABASE_URL to a sync one for Alembic.
db_url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url", ""))
db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
config.set_main_option("sqlalchemy.url", db_url)

# Import Base and all models so autogenerate sees the full schema.
from common.db import Base  # noqa: E402
import auth.models  # noqa: E402, F401
import workspaces.models  # noqa: E402, F401
import documents.models  # noqa: E402, F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection."""
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
