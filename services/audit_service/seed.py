"""Начальные данные Audit Service."""
import sqlite3


def seed_audit_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM activity_logs").fetchone()[0] > 0:
        return
    conn.executemany(
        """
        INSERT INTO activity_logs (id, entity_type, entity_id, user_id, action, old_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("log-001", "HYPOTHESIS", "hyp-001", "user-001", "CREATED", None, '{"status":"DRAFT"}', "2026-10-01T10:00:00Z"),
            ("log-002", "HYPOTHESIS", "hyp-001", "user-001", "STATUS_CHANGED", '{"status":"DRAFT"}', '{"status":"VALIDATION"}', "2026-10-03T09:00:00Z"),
        ],
    )
    conn.commit()
