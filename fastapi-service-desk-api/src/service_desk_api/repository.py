from __future__ import annotations

from collections.abc import Sequence

from .database import connection, now_iso
from .schemas import TicketCreate, TicketOut, TicketStatus


def _ticket(row: object) -> TicketOut:
    return TicketOut.model_validate(dict(row))


def create_ticket(payload: TicketCreate) -> TicketOut:
    timestamp = now_iso()
    with connection() as db:
        cursor = db.execute(
            "INSERT INTO tickets (title, description, priority, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'open', ?, ?)",
            (payload.title, payload.description, payload.priority, timestamp, timestamp),
        )
        row = db.execute("SELECT * FROM tickets WHERE id = ?", (cursor.lastrowid,)).fetchone()
        if row is None:
            raise RuntimeError("Created ticket could not be read back.")
        return _ticket(row)


def get_ticket(ticket_id: int) -> TicketOut | None:
    with connection() as db:
        row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return _ticket(row) if row is not None else None


def list_tickets(
    *, status: TicketStatus | None, search: str | None, limit: int, offset: int
) -> tuple[Sequence[TicketOut], int]:
    conditions: list[str] = []
    parameters: list[object] = []
    if status is not None:
        conditions.append("status = ?")
        parameters.append(status)
    if search:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        term = f"%{search}%"
        parameters.extend((term, term))
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with connection() as db:
        total = db.execute(f"SELECT COUNT(*) FROM tickets{where}", parameters).fetchone()[0]
        rows = db.execute(
            f"SELECT * FROM tickets{where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
            [*parameters, limit, offset],
        ).fetchall()
        return [_ticket(row) for row in rows], int(total)


def update_ticket_status(ticket_id: int, status: TicketStatus) -> TicketOut | None:
    timestamp = now_iso()
    with connection() as db:
        cursor = db.execute(
            "UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?",
            (status, timestamp, ticket_id),
        )
        if cursor.rowcount == 0:
            return None
        row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return _ticket(row) if row is not None else None


def delete_ticket(ticket_id: int) -> bool:
    with connection() as db:
        cursor = db.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        return cursor.rowcount > 0
