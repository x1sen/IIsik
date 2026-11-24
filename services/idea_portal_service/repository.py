"""Репозиторий Idea Portal Service (idea.db)."""
from __future__ import annotations
import sqlite3
from services.idea_portal_service.models import IdeaModel


class IdeaPortalRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                expected_effect TEXT NOT NULL,
                category TEXT NOT NULL,
                author_name TEXT NOT NULL,
                status TEXT NOT NULL,
                hypothesis_id TEXT
            );
            """
        )
        self._conn.commit()

    def list_ideas(self) -> list[IdeaModel]:
        rows = self._conn.execute("SELECT * FROM ideas").fetchall()
        return [IdeaModel(**dict(r)) for r in rows]

    def create_idea(self, idea: IdeaModel) -> IdeaModel:
        self._conn.execute(
            """
            INSERT INTO ideas (id, product_id, title, description, expected_effect, category, author_name, status, hypothesis_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea.id,
                idea.product_id,
                idea.title,
                idea.description,
                idea.expected_effect,
                idea.category,
                idea.author_name,
                idea.status,
                idea.hypothesis_id,
            ),
        )
        self._conn.commit()
        return idea
