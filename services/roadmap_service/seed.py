"""Начальные данные Roadmap Service."""
import json
import sqlite3


def seed_roadmap_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM roadmap_items").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO hypothesis_title_cache (hypothesis_id, title) VALUES (?, ?)",
        [
            ("hyp-001", "Упрощение анкеты онлайн-кредита до 3 шагов"),
            ("hyp-002", "Кэшбэк-подсказки при оплате картой в приложении"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO roadmap_items (id, hypothesis_id, start_date, end_date, duration, dependencies, assignee_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("road-001", "hyp-001", "2026-10-01", "2026-10-20", 20, json.dumps([]), "user-001"),
            ("road-002", "hyp-002", "2026-10-21", "2026-11-05", 16, json.dumps(["road-001"]), "user-001"),
        ],
    )
    conn.commit()
