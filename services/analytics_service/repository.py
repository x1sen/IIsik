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
