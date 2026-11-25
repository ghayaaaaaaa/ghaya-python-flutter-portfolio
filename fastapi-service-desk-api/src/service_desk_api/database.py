from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / ".local" / "service_desk.sqlite3"


def database_path() -> Path:
    configured = os.environ.get("SERVICE_DESK_DB_PATH")
    return Path(configured).expanduser() if configured else DEFAULT_DB_PATH


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def initialize_database() -> None:
    with connection() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 3 AND 120),
                description TEXT NOT NULL DEFAULT '' CHECK(length(description) <= 2000),
                priority TEXT NOT NULL CHECK(priority IN ('low', 'normal', 'high')),
                status TEXT NOT NULL CHECK(status IN ('open', 'in_progress', 'closed')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status_created ON tickets(status, created_at)")
