"""Репозиторий Notification Service (notification.db)."""
from __future__ import annotations
import sqlite3
from services.notification_service.models import NotificationModel


class NotificationRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                is_read INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def list_by_user(self, user_id: str, unread_only: bool = False) -> list[NotificationModel]:
        query = "SELECT * FROM notifications WHERE user_id = ?"
        params: list[str] = [user_id]
        if unread_only:
            query += " AND is_read = 0"
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [
            NotificationModel(
                id=r["id"],
                user_id=r["user_id"],
                type=r["type"],
                message=r["message"],
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                is_read=bool(r["is_read"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def create_notification(self, item: NotificationModel) -> NotificationModel:
        self._conn.execute(
            """
            INSERT INTO notifications (id, user_id, type, message, entity_type, entity_id, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.user_id,
                item.type,
                item.message,
                item.entity_type,
                item.entity_id,
                1 if item.is_read else 0,
                item.created_at,
            ),
        )
        self._conn.commit()
        return item

    def mark_read(self, notification_id: str) -> NotificationModel | None:
        cur = self._conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,)
        )
        self._conn.commit()
        if cur.rowcount == 0:
            return None
        row = self._conn.execute(
            "SELECT * FROM notifications WHERE id = ?", (notification_id,)
        ).fetchone()
        if row is None:
            return None
        return NotificationModel(
            id=row["id"],
            user_id=row["user_id"],
            type=row["type"],
            message=row["message"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            is_read=bool(row["is_read"]),
            created_at=row["created_at"],
        )
