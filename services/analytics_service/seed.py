"""Начальные данные Analytics Service."""
import sqlite3


def seed_analytics_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM dashboard_metrics").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO dashboard_metrics (id, metric_type, product_id, period, value) VALUES (?, ?, ?, ?, ?)",
        [
            ("met-001", "CONVERSION_RATE", "prod-001", "2026-Q4", 0.42),
            ("met-002", "P1_INITIATIVES_COUNT", "prod-001", "2026-Q4", 3.0),
            ("met-003", "AVG_VALIDATION_DAYS", "prod-002", "2026-Q4", 11.5),
        ],
    )
    conn.executemany(
        "INSERT INTO analytics_read_model (hypothesis_id, product_id, status, priority, rice_score, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("hyp-001", "prod-001", "VALIDATION", "P1", 144.0, "2026-10-03T09:00:00Z"),
            ("hyp-002", "prod-002", "CONFIRMED", "P1", 120.0, "2026-10-14T18:05:00Z"),
        ],
    )
    conn.commit()
