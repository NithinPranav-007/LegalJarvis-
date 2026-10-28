"""Integration tests for Alembic schema migrations."""

import os
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config


def test_alembic_migrations_lifecycle() -> None:
    backend_dir = Path(__file__).resolve().parent.parent.parent
    alembic_ini = backend_dir / "alembic.ini"

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        sqlite_url = f"sqlite:///{db_path}"
        cfg = Config(str(alembic_ini))
        cfg.set_main_option("sqlalchemy.url", sqlite_url)

        # 1. Upgrade to head
        command.upgrade(cfg, "head")

        # 2. Downgrade to base
        command.downgrade(cfg, "base")

        # 3. Upgrade to head again
        command.upgrade(cfg, "head")
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
