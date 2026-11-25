from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS steps (
                    action_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    position INTEGER NOT NULL,
                    step_id TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    requires_approval INTEGER NOT NULL,
                    approval TEXT NOT NULL DEFAULT 'not-required',
                    status TEXT NOT NULL,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(run_id, step_id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES runs(run_id),
                    action_id TEXT,
                    event_type TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def create_run(self, run_id: str, goal: str, steps: list[dict[str, Any]]) -> None:
        timestamp = now_iso()
        with self._connect() as db:
            db.execute(
                "INSERT INTO runs(run_id, goal, status, created_at) VALUES (?, ?, ?, ?)",
                (run_id, goal, "running", timestamp),
            )
            for position, step in enumerate(steps):
                action_id = f"{run_id}:{step['step_id']}"
                db.execute(
                    """INSERT INTO steps(
                        action_id, run_id, position, step_id, tool, arguments_json,
                        requires_approval, approval, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        action_id,
                        run_id,
                        position,
                        step["step_id"],
                        step["tool"],
                        json.dumps(step["arguments"], ensure_ascii=False),
                        int(step["requires_approval"]),
                        "required" if step["requires_approval"] else "not-required",
                        "queued",
                        timestamp,
                    ),
                )
            self._event(db, run_id, None, "plan_created", {"step_count": len(steps)})

    @staticmethod
    def _event(
        db: sqlite3.Connection,
        run_id: str,
        action_id: str | None,
        event_type: str,
        details: dict[str, Any],
    ) -> None:
        db.execute(
            """INSERT INTO events(run_id, action_id, event_type, details_json, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                run_id,
                action_id,
                event_type,
                json.dumps(details, ensure_ascii=False, sort_keys=True),
                now_iso(),
            ),
        )

    def queued_steps(self, run_id: str) -> list[sqlite3.Row]:
        with self._connect() as db:
            return db.execute(
                "SELECT * FROM steps WHERE run_id = ? AND status IN ('queued', 'pending') ORDER BY position",
                (run_id,),
            ).fetchall()

    def get_step(self, action_id: str) -> sqlite3.Row | None:
        with self._connect() as db:
            return db.execute("SELECT * FROM steps WHERE action_id = ?", (action_id,)).fetchone()

    def run_status(self, run_id: str) -> str | None:
        with self._connect() as db:
            row = db.execute("SELECT status FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return None if row is None else str(row["status"])

    def completed_results(self, run_id: str) -> dict[str, dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT step_id, result_json FROM steps WHERE run_id = ? AND status = 'completed'",
                (run_id,),
            ).fetchall()
        return {
            row["step_id"]: json.loads(row["result_json"])
            for row in rows
            if row["result_json"] is not None
        }

    def mark_pending(self, action_id: str) -> None:
        with self._connect() as db:
            step = db.execute("SELECT run_id, status FROM steps WHERE action_id = ?", (action_id,)).fetchone()
            if step is None or step["status"] not in ("queued", "pending"):
                return
            db.execute("UPDATE steps SET status = 'pending' WHERE action_id = ?", (action_id,))
            self._event(db, step["run_id"], action_id, "approval_required", {})
            db.execute("UPDATE runs SET status = 'waiting_approval' WHERE run_id = ?", (step["run_id"],))

    def mark_approved(self, action_id: str) -> sqlite3.Row:
        with self._connect() as db:
            step = db.execute("SELECT * FROM steps WHERE action_id = ?", (action_id,)).fetchone()
            if step is None:
                raise KeyError("Unknown action ID.")
            if step["status"] == "completed":
                return step
            if not step["requires_approval"] or step["status"] != "pending":
                raise ValueError("Only a pending approval-gated action can be approved.")
            db.execute(
                "UPDATE steps SET approval = 'approved', status = 'queued' WHERE action_id = ?",
                (action_id,),
            )
            self._event(db, step["run_id"], action_id, "approved", {})
            db.execute("UPDATE runs SET status = 'running' WHERE run_id = ?", (step["run_id"],))
            return db.execute("SELECT * FROM steps WHERE action_id = ?", (action_id,)).fetchone()

    def mark_rejected(self, action_id: str) -> None:
        with self._connect() as db:
            step = db.execute("SELECT run_id, status FROM steps WHERE action_id = ?", (action_id,)).fetchone()
            if step is None:
                raise KeyError("Unknown action ID.")
            if step["status"] != "pending":
                raise ValueError("Only a pending action can be rejected.")
            db.execute(
                "UPDATE steps SET approval = 'rejected', status = 'rejected' WHERE action_id = ?",
                (action_id,),
            )
            self._event(db, step["run_id"], action_id, "rejected", {})
            db.execute("UPDATE runs SET status = 'rejected' WHERE run_id = ?", (step["run_id"],))

    def mark_started(self, action_id: str) -> sqlite3.Row:
        with self._connect() as db:
            step = db.execute("SELECT * FROM steps WHERE action_id = ?", (action_id,)).fetchone()
            if step is None:
                raise KeyError("Unknown action ID.")
            if step["status"] == "completed":
                return step
            if step["status"] != "queued":
                raise ValueError("The action is not ready to execute.")
            db.execute("UPDATE steps SET status = 'running' WHERE action_id = ?", (action_id,))
            self._event(db, step["run_id"], action_id, "started", {"tool": step["tool"]})
            return db.execute("SELECT * FROM steps WHERE action_id = ?", (action_id,)).fetchone()

    def mark_completed(self, action_id: str, result: dict[str, Any]) -> None:
        with self._connect() as db:
            step = db.execute("SELECT run_id FROM steps WHERE action_id = ?", (action_id,)).fetchone()
            db.execute(
                "UPDATE steps SET status = 'completed', result_json = ? WHERE action_id = ?",
                (json.dumps(result, ensure_ascii=False), action_id),
            )
            self._event(db, step["run_id"], action_id, "completed", {"result_keys": sorted(result)})

    def mark_failed(self, action_id: str, error_type: str) -> None:
        with self._connect() as db:
            step = db.execute("SELECT run_id FROM steps WHERE action_id = ?", (action_id,)).fetchone()
            db.execute("UPDATE steps SET status = 'failed' WHERE action_id = ?", (action_id,))
            self._event(db, step["run_id"], action_id, "failed", {"error_type": error_type})
            db.execute("UPDATE runs SET status = 'failed' WHERE run_id = ?", (step["run_id"],))

    def mark_run_complete(self, run_id: str) -> None:
        with self._connect() as db:
            pending = db.execute(
                "SELECT COUNT(*) FROM steps WHERE run_id = ? AND status IN ('queued', 'pending', 'running')",
                (run_id,),
            ).fetchone()[0]
            failed = db.execute(
                "SELECT COUNT(*) FROM steps WHERE run_id = ? AND status IN ('failed', 'rejected')",
                (run_id,),
            ).fetchone()[0]
            status = "failed" if failed else ("completed" if pending == 0 else "running")
            db.execute("UPDATE runs SET status = ? WHERE run_id = ?", (status, run_id))

    def pending_actions(self) -> list[sqlite3.Row]:
        with self._connect() as db:
            return db.execute(
                """SELECT steps.*, runs.goal FROM steps JOIN runs USING(run_id)
                   WHERE steps.status = 'pending' ORDER BY steps.created_at"""
            ).fetchall()

