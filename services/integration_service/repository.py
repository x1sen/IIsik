"""Репозиторий Integration Service (integration.db)."""
from __future__ import annotations
import sqlite3
from typing import Optional
from services.integration_service.models import BacklogTaskModel


class IntegrationRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS backlog_tasks (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL UNIQUE,
                idempotency_key TEXT NOT NULL UNIQUE,
                external_system TEXT NOT NULL,
                external_key TEXT NOT NULL,
                external_url TEXT NOT NULL,
                status TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def get_by_hypothesis(self, hypothesis_id: str) -> Optional[BacklogTaskModel]:
        row = self._conn.execute(
            "SELECT * FROM backlog_tasks WHERE hypothesis_id = ?", (hypothesis_id,)
        ).fetchone()
        return BacklogTaskModel(**dict(row)) if row else None

    def create_task(self, task: BacklogTaskModel) -> BacklogTaskModel:
        self._conn.execute(
            """
            INSERT INTO backlog_tasks (id, hypothesis_id, idempotency_key, external_system, external_key, external_url, status, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.id,
                task.hypothesis_id,
                task.idempotency_key,
                task.external_system,
                task.external_key,
                task.external_url,
                task.status,
                task.synced_at,
            ),
        )
        self._conn.commit()
        return task
