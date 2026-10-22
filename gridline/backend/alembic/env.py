"""Alembic environment.

Migrations run synchronously (psycopg2) even though the app is async, because
alembic's offline/online modes and most tooling assume a sync driver. The URL
is rewritten from the app's asyncpg URL at import time.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.db import Base
from app import models  # noqa: F401  (import registers the tables on Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

sync_url = settings.database_url.replace("+asyncpg", "").replace(
    "postgresql://", "postgresql+psycopg2://"
)
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):
    # GeoAlchemy2 creates its own spatial index and the geometry_columns view;
    # excluding them keeps autogenerate from trying to drop PostGIS internals.
    if type_ == "table" and name in {"spatial_ref_sys", "geometry_columns", "geography_columns"}:
        return False
    if type_ == "index" and name and name.startswith("idx_") and "geom" in name:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
