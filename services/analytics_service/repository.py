"""Репозиторий Analytics Service (analytics.db)."""
from __future__ import annotations
import sqlite3
from typing import Optional
from services.analytics_service.models import DashboardMetricModel


class AnalyticsRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dashboard_metrics (
                id TEXT PRIMARY KEY,
                metric_type TEXT NOT NULL,
                product_id TEXT NOT NULL,
                period TEXT NOT NULL,
                value REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS analytics_read_model (
                hypothesis_id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                rice_score REAL,
                updated_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def list_metrics(
        self, product_id: Optional[str] = None, period: Optional[str] = None
    ) -> list[DashboardMetricModel]:
        query = "SELECT * FROM dashboard_metrics WHERE 1=1"
        params: list[str] = []
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        if period:
            query += " AND period = ?"
            params.append(period)
        rows = self._conn.execute(query, params).fetchall()
        return [DashboardMetricModel(**dict(r)) for r in rows]

    def upsert_read_model_and_recalculate(
        self,
        hypothesis_id: str,
        product_id: str,
        status: Optional[str],
        priority: Optional[str],
        rice_score: Optional[float],
        updated_at: str,
    ) -> None:
        existing = self._conn.execute(
            "SELECT * FROM analytics_read_model WHERE hypothesis_id = ?", (hypothesis_id,)
        ).fetchone()
        new_status = status if status is not None else (existing["status"] if existing else "DRAFT")
        new_priority = priority if priority is not None else (existing["priority"] if existing else "P2")
        new_rice = rice_score if rice_score is not None else (existing["rice_score"] if existing else None)
        self._conn.execute(
            """
            INSERT INTO analytics_read_model (hypothesis_id, product_id, status, priority, rice_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hypothesis_id) DO UPDATE SET
                status = excluded.status,
                priority = excluded.priority,
                rice_score = excluded.rice_score,
                updated_at = excluded.updated_at
            """,
            (hypothesis_id, product_id, new_status, new_priority, new_rice, updated_at),
        )
        p1_count = self._conn.execute(
            "SELECT COUNT(*) FROM analytics_read_model WHERE product_id = ? AND priority = 'P1'",
            (product_id,),
        ).fetchone()[0]
        self._conn.execute(
            """
            INSERT INTO dashboard_metrics (id, metric_type, product_id, period, value)
            VALUES (?, 'P1_INITIATIVES_COUNT', ?, '2026-Q4', ?)
            ON CONFLICT(id) DO UPDATE SET value = excluded.value
            """,
            (f"met-p1-{product_id}", product_id, float(p1_count)),
        )
        self._conn.commit()
