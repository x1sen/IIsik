"""Начальные данные Report Service."""
import sqlite3


def seed_report_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0] > 0:
        return
    conn.execute(
        """
        INSERT INTO reports (id, research_id, conclusion, recommendations, file_url, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "rep-001",
            "res-002",
            "Гипотеза подтверждена: 74% респондентов не замечают текущий блок кэшбэка.",
            "Вынести виджет активных категорий на главный экран платежей.",
            "s3://pdp-reports/rep-001.pdf",
            "2026-10-14T18:00:00Z",
        ),
    )
    conn.commit()
