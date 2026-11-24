"""Репозиторий Audit Service (audit.db)."""
from __future__ import annotations
import sqlite3
from services.audit_service.models import ActivityLogModel


class AuditRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def list_logs(self, entity_type: str, entity_id: str) -> list[ActivityLogModel]:
        rows = self._conn.execute(
            "SELECT * FROM activity_logs WHERE entity_type = ? AND entity_id = ? ORDER BY timestamp ASC",
            (entity_type, entity_id),
        ).fetchall()
        return [ActivityLogModel(**dict(r)) for r in rows]

    def create_log(self, log: ActivityLogModel) -> ActivityLogModel:
        self._conn.execute(
            """
            INSERT INTO activity_logs (id, entity_type, entity_id, user_id, action, old_value, new_value, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.id,
                log.entity_type,
                log.entity_id,
                log.user_id,
                log.action,
                log.old_value,
                log.new_value,
                log.timestamp,
            ),
        )
        self._conn.commit()
        return log
