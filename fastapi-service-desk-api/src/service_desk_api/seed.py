from __future__ import annotations

from .database import connection, now_iso

SAMPLE_TICKETS = (
    ("Add an export option", "Allow a coordinator to export a filtered report.", "normal"),
    ("Check delayed notifications", "Review a synthetic example of a delayed status update.", "high"),
    ("Improve search labels", "Clarify the labels shown above the ticket search field.", "low"),
)


def seed() -> int:
    timestamp = now_iso()
    inserted = 0
    with connection() as db:
        for title, description, priority in SAMPLE_TICKETS:
            exists = db.execute("SELECT 1 FROM tickets WHERE title = ?", (title,)).fetchone()
            if exists:
                continue
            db.execute(
                "INSERT INTO tickets (title, description, priority, status, created_at, updated_at) "
                "VALUES (?, ?, ?, 'open', ?, ?)",
                (title, description, priority, timestamp, timestamp),
            )
            inserted += 1
    return inserted


if __name__ == "__main__":
    print(f"Inserted {seed()} synthetic tickets.")
