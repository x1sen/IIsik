"""Репозиторий Auth Service (auth.sqlite3)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from services.auth_service.models import AuthUserModel


class AuthRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS auth_users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def get_by_id(self, user_id: str) -> Optional[AuthUserModel]:
        row = self._conn.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
        return AuthUserModel(**dict(row)) if row else None

    def get_by_email(self, email: str) -> Optional[AuthUserModel]:
        row = self._conn.execute(
            "SELECT * FROM auth_users WHERE LOWER(email) = LOWER(?)", (email,)
        ).fetchone()
        return AuthUserModel(**dict(row)) if row else None

    def create_user(self, user: AuthUserModel) -> AuthUserModel:
        self._conn.execute(
            """
            INSERT INTO auth_users (id, name, email, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user.id, user.name, user.email, user.password_hash, user.role, user.created_at),
        )
        self._conn.commit()
        return user
