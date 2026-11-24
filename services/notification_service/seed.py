"""Начальные данные Notification Service."""
import sqlite3


def seed_notification_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] > 0:
        return
    conn.executemany(
        """
        INSERT INTO notifications (id, user_id, type, message, entity_type, entity_id, is_read, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("not-001", "user-001", "IN_APP", "Отчёт по исследованию res-002 готов к просмотру.", "REPORT", "rep-001", 0, "2026-10-14T18:01:00Z"),
            ("not-002", "user-001", "IN_APP", "Елена Ковалёва добавила комментарий к гипотезе hyp-001.", "HYPOTHESIS", "hyp-001", 1, "2026-10-02T14:21:00Z"),
        ],
    )
    conn.commit()
