"""Репозиторий Hypothesis Service (изолированная БД hypothesis.db)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from services.hypothesis_service.models import (
    CommentModel,
    HypothesisModel,
    HypothesisTemplateModel,
    RICEScoreModel,
)


class HypothesisRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                rice_score REAL,
                product_id TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS hypothesis_templates (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL UNIQUE,
                if_action TEXT NOT NULL,
                then_result TEXT NOT NULL,
                because_assumption TEXT NOT NULL,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
            );
            CREATE TABLE IF NOT EXISTS rice_scores (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL UNIQUE,
                reach INTEGER NOT NULL,
                impact REAL NOT NULL,
                confidence REAL NOT NULL,
                effort INTEGER NOT NULL,
                calculated_score REAL NOT NULL,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
            );
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                author_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def count_hypotheses(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS cnt FROM hypotheses").fetchone()
        return int(row["cnt"])

    def get_by_id(self, hypothesis_id: str) -> Optional[HypothesisModel]:
        row = self._conn.execute(
            "SELECT * FROM hypotheses WHERE id = ?", (hypothesis_id,)
        ).fetchone()
        return HypothesisModel(**dict(row)) if row else None

    def list_hypotheses(
        self,
        product_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        owner_id: Optional[str] = None,
        min_rice_score: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "DESC",
    ) -> list[HypothesisModel]:
        query = "SELECT * FROM hypotheses WHERE 1=1"
        params: list[object] = []
        if product_id:
            query += " AND product_id = ?"
            params.append(product_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if owner_id:
            query += " AND owner_id = ?"
            params.append(owner_id)
        if min_rice_score is not None:
            query += " AND rice_score IS NOT NULL AND rice_score >= ?"
            params.append(min_rice_score)
        if search and search.strip():
            like = f"%{search.strip()}%"
            query += " AND (LOWER(title) LIKE LOWER(?) OR LOWER(description) LIKE LOWER(?))"
            params.extend([like, like])

        allowed_sort = {
            "created_at": "created_at",
            "rice_score": "COALESCE(rice_score, -1)",
            "priority": "priority",
            "title": "title",
        }
        order_col = allowed_sort.get(sort_by, "created_at")
        order_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"
        query += f" ORDER BY {order_col} {order_dir}"
        rows = self._conn.execute(query, params).fetchall()
        return [HypothesisModel(**dict(r)) for r in rows]

    def create_hypothesis(
        self, hypothesis: HypothesisModel, template: HypothesisTemplateModel
    ) -> HypothesisModel:
        self._conn.execute(
            """
            INSERT INTO hypotheses (id, title, description, status, priority, rice_score, product_id, owner_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hypothesis.id,
                hypothesis.title,
                hypothesis.description,
                hypothesis.status,
                hypothesis.priority,
                hypothesis.rice_score,
                hypothesis.product_id,
                hypothesis.owner_id,
                hypothesis.created_at,
            ),
        )
        self._conn.execute(
            """
            INSERT INTO hypothesis_templates (id, hypothesis_id, if_action, then_result, because_assumption)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                template.id,
                template.hypothesis_id,
                template.if_action,
                template.then_result,
                template.because_assumption,
            ),
        )
        self._conn.commit()
        return hypothesis

    def save_rice_score(self, score: RICEScoreModel, new_status: Optional[str] = None) -> RICEScoreModel:
        self._conn.execute(
            """
            INSERT INTO rice_scores (id, hypothesis_id, reach, impact, confidence, effort, calculated_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hypothesis_id) DO UPDATE SET
                reach = excluded.reach,
                impact = excluded.impact,
                confidence = excluded.confidence,
                effort = excluded.effort,
                calculated_score = excluded.calculated_score
            """,
            (
                score.id,
                score.hypothesis_id,
                score.reach,
                score.impact,
                score.confidence,
                score.effort,
                score.calculated_score,
            ),
        )
        if new_status:
            self._conn.execute(
                "UPDATE hypotheses SET rice_score = ?, status = ? WHERE id = ?",
                (score.calculated_score, new_status, score.hypothesis_id),
            )
        else:
            self._conn.execute(
                "UPDATE hypotheses SET rice_score = ? WHERE id = ?",
                (score.calculated_score, score.hypothesis_id),
            )
        self._conn.commit()
        return score

    def update_status(self, hypothesis_id: str, new_status: str) -> HypothesisModel:
        self._conn.execute(
            "UPDATE hypotheses SET status = ? WHERE id = ?", (new_status, hypothesis_id)
        )
        self._conn.commit()
        updated = self.get_by_id(hypothesis_id)
        assert updated is not None
        return updated

    def add_comment(self, comment: CommentModel) -> CommentModel:
        self._conn.execute(
            """
            INSERT INTO comments (id, entity_type, entity_id, author_id, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                comment.id,
                comment.entity_type,
                comment.entity_id,
                comment.author_id,
                comment.text,
                comment.created_at,
            ),
        )
        self._conn.commit()
        return comment

    def get_template_by_hypothesis(self, hypothesis_id: str) -> Optional[HypothesisTemplateModel]:
        row = self._conn.execute(
            "SELECT * FROM hypothesis_templates WHERE hypothesis_id = ?", (hypothesis_id,)
        ).fetchone()
        return HypothesisTemplateModel(**dict(row)) if row else None

    def get_rice_by_hypothesis(self, hypothesis_id: str) -> Optional[RICEScoreModel]:
        row = self._conn.execute(
            "SELECT * FROM rice_scores WHERE hypothesis_id = ?", (hypothesis_id,)
        ).fetchone()
        return RICEScoreModel(**dict(row)) if row else None

    def list_comments(self, entity_type: str, entity_id: str) -> list[CommentModel]:
        rows = self._conn.execute(
            "SELECT * FROM comments WHERE entity_type = ? AND entity_id = ? ORDER BY created_at ASC",
            (entity_type, entity_id),
        ).fetchall()
        return [CommentModel(**dict(r)) for r in rows]
