"""Репозиторий File Storage Service (file_storage.db)."""
from __future__ import annotations
import sqlite3
from services.file_storage_service.models import AttachmentModel


class FileStorageRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS attachments (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_url TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_by TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def list_by_entity(self, entity_type: str, entity_id: str) -> list[AttachmentModel]:
        rows = self._conn.execute(
            "SELECT * FROM attachments WHERE entity_type = ? AND entity_id = ?",
            (entity_type, entity_id),
        ).fetchall()
        return [AttachmentModel(**dict(r)) for r in rows]
