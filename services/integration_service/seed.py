"""Начальные данные Integration Service."""
import sqlite3


def seed_integration_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM backlog_tasks").fetchone()[0] > 0:
        return
    conn.execute(
        """
        INSERT INTO backlog_tasks (id, hypothesis_id, idempotency_key, external_system, external_key, external_url, status, synced_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "bt-001",
            "hyp-002",
            "hyp-002",
            "TASK_TRACKER",
            "PD-412",
            "https://tracker.bank.local/browse/PD-412",
            "IN_PROGRESS",
            "2026-10-15T10:00:00Z",
        ),
    )
    conn.commit()
