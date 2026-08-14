"""
Alembic environment script for EngineerAI.

Customized from Alembic's default `env.py` template in three ways:

1. The database URL comes from the app's own centralized settings
   (Task 3's `app.core.config.settings`), not a hardcoded value in
   alembic.ini — one source of truth for DATABASE_URL.
2. A naming convention is applied to SQLModel's metadata BEFORE the model
   classes are imported, so constraints get predictable names — required
   for SQLite's "batch mode" (recreate-and-copy) to work correctly on
   future migrations that alter existing tables, not just create new ones.
3. `render_as_batch=True` is enabled for SQLite compatibility with future
   ALTER-style migrations.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from app.core.config import settings

# --- Naming convention: must be set BEFORE importing the models ----------
# Setting this after the model classes are imported would be too late —
# their tables/constraints are constructed at import time.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
SQLModel.metadata.naming_convention = NAMING_CONVENTION

# Now import the models package so every table registers against the
# (already-configured) shared metadata.
from app.db.models import Conversation, Message, Project, User  # noqa: E402,F401

# this is the Alembic Config object, which provides access to values within
# the .ini file in use.
config = context.config

# Override the ini file's placeholder URL with the app's real settings.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emits SQL without a live DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # required for SQLite ALTER support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connects to the database directly)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # required for SQLite ALTER support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
