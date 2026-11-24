"""Репозиторий Research Service (изолированная БД research.db)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from services.research_service.models import (
    InsightModel,
    ResearchDesignModel,
    ResearchModel,
    ResearchNoteModel,
)


class ResearchRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS researches (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                type TEXT NOT NULL,
                method TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                sample_size INTEGER NOT NULL,
                start_date TEXT,
                end_date TEXT,
                hypothesis_id TEXT NOT NULL,
                assignee_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS research_designs (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL UNIQUE,
                goal TEXT NOT NULL,
                questions TEXT NOT NULL,
                success_criteria TEXT NOT NULL,
                user_stories TEXT,
                FOREIGN KEY (research_id) REFERENCES researches(id)
            );
            CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (research_id) REFERENCES researches(id)
            );
            CREATE TABLE IF NOT EXISTS research_notes (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                text TEXT NOT NULL,
                author_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (research_id) REFERENCES researches(id)
            );
            """
        )
        self._conn.commit()

    def get_by_id(self, research_id: str) -> Optional[ResearchModel]:
        row = self._conn.execute("SELECT * FROM researches WHERE id = ?", (research_id,)).fetchone()
        return ResearchModel(**dict(row)) if row else None

    def list_researches(
        self,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        sort_by: str = "start_date",
        sort_dir: str = "DESC",
    ) -> list[ResearchModel]:
        query = "SELECT * FROM researches WHERE 1=1"
        params: list[str] = []
        if hypothesis_id:
            query += " AND hypothesis_id = ?"
            params.append(hypothesis_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if assignee_id:
            query += " AND assignee_id = ?"
            params.append(assignee_id)
        allowed_sort = {
            "start_date": "COALESCE(start_date, '')",
            "status": "status",
            "title": "title",
            "sample_size": "sample_size",
        }
        order_col = allowed_sort.get(sort_by, "COALESCE(start_date, '')")
        order_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"
        query += f" ORDER BY {order_col} {order_dir}"
        rows = self._conn.execute(query, params).fetchall()
        return [ResearchModel(**dict(r)) for r in rows]

    def create_research(
        self, research: ResearchModel, design: ResearchDesignModel
    ) -> ResearchModel:
        self._conn.execute(
            """
            INSERT INTO researches (id, title, status, type, method, target_audience, sample_size, start_date, end_date, hypothesis_id, assignee_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                research.id,
                research.title,
                research.status,
                research.type,
                research.method,
                research.target_audience,
                research.sample_size,
                research.start_date,
                research.end_date,
                research.hypothesis_id,
                research.assignee_id,
            ),
        )
        self._conn.execute(
            """
            INSERT INTO research_designs (id, research_id, goal, questions, success_criteria, user_stories)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                design.id,
                design.research_id,
                design.goal,
                design.questions,
                design.success_criteria,
                design.user_stories,
            ),
        )
        self._conn.commit()
        return research

    def update_status(self, research_id: str, new_status: str, end_date: Optional[str] = None) -> ResearchModel:
        if end_date:
            self._conn.execute(
                "UPDATE researches SET status = ?, end_date = ? WHERE id = ?",
                (new_status, end_date, research_id),
            )
        else:
            self._conn.execute(
                "UPDATE researches SET status = ? WHERE id = ?",
                (new_status, research_id),
            )
        self._conn.commit()
        updated = self.get_by_id(research_id)
        assert updated is not None
        return updated

    def add_insight(self, insight: InsightModel, new_status: Optional[str] = None) -> InsightModel:
        self._conn.execute(
            "INSERT INTO insights (id, research_id, text, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            (insight.id, insight.research_id, insight.text, insight.created_by, insight.created_at),
        )
        if new_status:
            self._conn.execute(
                "UPDATE researches SET status = ? WHERE id = ?", (new_status, insight.research_id)
            )
        self._conn.commit()
        return insight

    def add_note(self, note: ResearchNoteModel, new_status: Optional[str] = None) -> ResearchNoteModel:
        self._conn.execute(
            "INSERT INTO research_notes (id, research_id, text, author_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (note.id, note.research_id, note.text, note.author_id, note.created_at),
        )
        if new_status:
            self._conn.execute(
                "UPDATE researches SET status = ? WHERE id = ?", (new_status, note.research_id)
            )
        self._conn.commit()
        return note

    def get_design(self, research_id: str) -> Optional[ResearchDesignModel]:
        row = self._conn.execute(
            "SELECT * FROM research_designs WHERE research_id = ?", (research_id,)
        ).fetchone()
        return ResearchDesignModel(**dict(row)) if row else None

    def list_insights(self, research_id: str) -> list[InsightModel]:
        rows = self._conn.execute(
            "SELECT * FROM insights WHERE research_id = ? ORDER BY created_at ASC", (research_id,)
        ).fetchall()
        return [InsightModel(**dict(r)) for r in rows]

    def list_notes(self, research_id: str) -> list[ResearchNoteModel]:
        rows = self._conn.execute(
            "SELECT * FROM research_notes WHERE research_id = ? ORDER BY created_at ASC", (research_id,)
        ).fetchall()
        return [ResearchNoteModel(**dict(r)) for r in rows]
