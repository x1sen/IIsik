"""Репозиторий User Service (user.db)."""
from __future__ import annotations
import sqlite3
from typing import Optional
from services.user_service.models import UserModel


class UserRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                team_id TEXT,
                expertise TEXT
            );
            """
        )
        self._conn.commit()

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        row = self._conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return UserModel(**dict(row)) if row else None

    def list_users(self) -> list[UserModel]:
        rows = self._conn.execute("SELECT * FROM users").fetchall()
        return [UserModel(**dict(r)) for r in rows]
