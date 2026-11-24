"""Начальные данные Idea Portal Service."""
import sqlite3


def seed_idea_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0] > 0:
        return
    conn.execute(
        """
        INSERT INTO ideas (id, product_id, title, description, expected_effect, category, author_name, status, hypothesis_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "idea-001",
            "prod-001",
            "Автозаполнение УНП для корпоративных клиентов",
            "При создании платёжки в РКО подтягивать реквизиты из ЕГР по УНП.",
            "Сокращение времени заполнения платёжного поручения на 40%.",
            "Корпоративный бизнес",
            "Иван Петров (отдел продаж)",
            "CONVERTED",
            "hyp-003",
        ),
    )
    conn.commit()
