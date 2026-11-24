"""Репозиторий Roadmap Service (roadmap.db)."""
from __future__ import annotations
import json
import sqlite3
from services.roadmap_service.models import RoadmapItemModel


class RoadmapRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS roadmap_items (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL UNIQUE,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                duration INTEGER NOT NULL,
                dependencies TEXT,
                assignee_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS hypothesis_title_cache (
                hypothesis_id TEXT PRIMARY KEY,
                title TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def list_items(self, sort_dir: str = "ASC") -> list[RoadmapItemModel]:
        order = "DESC" if sort_dir.upper() == "DESC" else "ASC"
        rows = self._conn.execute(
            f"""
            SELECT r.*, COALESCE(c.title, '') AS hypothesis_title
            FROM roadmap_items r
            LEFT JOIN hypothesis_title_cache c ON r.hypothesis_id = c.hypothesis_id
            ORDER BY r.start_date {order}
            """
        ).fetchall()
        result: list[RoadmapItemModel] = []
        for r in rows:
            deps = json.loads(r["dependencies"]) if r["dependencies"] else []
            result.append(
                RoadmapItemModel(
                    id=r["id"],
                    hypothesis_id=r["hypothesis_id"],
                    hypothesis_title=r["hypothesis_title"],
                    start_date=r["start_date"],
                    end_date=r["end_date"],
                    duration=r["duration"],
                    dependencies=deps,
                    assignee_id=r["assignee_id"],
                )
            )
        return result

    def save_item(self, item: RoadmapItemModel) -> RoadmapItemModel:
        self._conn.execute(
            """
            INSERT INTO hypothesis_title_cache (hypothesis_id, title)
            VALUES (?, ?)
            ON CONFLICT(hypothesis_id) DO UPDATE SET title = excluded.title
            """,
            (item.hypothesis_id, item.hypothesis_title),
        )
        self._conn.execute(
            """
            INSERT INTO roadmap_items (id, hypothesis_id, start_date, end_date, duration, dependencies, assignee_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hypothesis_id) DO UPDATE SET
                start_date = excluded.start_date,
                end_date = excluded.end_date,
                duration = excluded.duration,
                dependencies = excluded.dependencies,
                assignee_id = excluded.assignee_id
            """,
            (
                item.id,
                item.hypothesis_id,
                item.start_date,
                item.end_date,
                item.duration,
                json.dumps(item.dependencies),
                item.assignee_id,
            ),
        )
        self._conn.commit()
        return item

    def upsert_title_cache(self, hypothesis_id: str, title: str) -> None:
        self._conn.execute(
            """
            INSERT INTO hypothesis_title_cache (hypothesis_id, title)
            VALUES (?, ?)
            ON CONFLICT(hypothesis_id) DO UPDATE SET title = excluded.title
            """,
            (hypothesis_id, title),
        )
        self._conn.commit()
