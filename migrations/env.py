"""
Alembic env.py — configured for AI Sales Assistant.

Key behaviours:
  - DATABASE_URL is loaded from .env (never hardcoded in alembic.ini)
  - All SQLAlchemy models are imported so autogenerate can detect schema changes
  - Supports both offline (SQL script) and online (live DB) migration modes
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Make sure 'app' package is importable ──────────────────────────────────
# (Alembic is run from the project root, so this is already usually on the path,
#  but we add it explicitly for robustness.)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ── Load .env so DATABASE_URL is available ─────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Import ALL models so autogenerate can detect them ─────────────────────
from app.db.session import Base          # noqa: F401 — Base must be imported first
import app.models.user                   # noqa: F401
import app.models.lead                   # noqa: F401
import app.models.conversation           # noqa: F401
from app.services.approval_service import PendingApproval  # noqa: F401

# ── Alembic config ─────────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with the value from .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./aisales.db")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


# ── Migration runners ──────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Generate a SQL script without a live DB connection.
    Useful for reviewing or running migrations manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,        # required for SQLite ALTER support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations against a live DB connection.
    This is the standard mode used by `alembic upgrade head`.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,    # required for SQLite ALTER support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
