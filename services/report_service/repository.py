"""Репозиторий Report Service (report.db)."""
from __future__ import annotations
import sqlite3
from typing import Optional
from services.report_service.models import ReportModel


class ReportRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL UNIQUE,
                conclusion TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                file_url TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def get_by_research(self, research_id: str) -> Optional[ReportModel]:
        row = self._conn.execute("SELECT * FROM reports WHERE research_id = ?", (research_id,)).fetchone()
        return ReportModel(**dict(row)) if row else None

    def get_by_id(self, report_id: str) -> Optional[ReportModel]:
        row = self._conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        return ReportModel(**dict(row)) if row else None

    def create_report(self, report: ReportModel) -> ReportModel:
        self._conn.execute(
            """
            INSERT INTO reports (id, research_id, conclusion, recommendations, file_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                report.id,
                report.research_id,
                report.conclusion,
                report.recommendations,
                report.file_url,
                report.created_at,
            ),
        )
        self._conn.commit()
        return report
