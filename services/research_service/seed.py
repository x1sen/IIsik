"""Начальные тестовые данные для Research Service."""

import sqlite3


def seed_research_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM researches").fetchone()[0] > 0:
        return

    conn.executemany(
        """
        INSERT INTO researches (id, title, status, type, method, target_audience, sample_size, start_date, end_date, hypothesis_id, assignee_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "res-001",
                "Юзабилити-тест 3-шаговой анкеты кредита",
                "IN_PROGRESS",
                "QUALITATIVE",
                "Глубинное интервью + тест прототипа",
                "Клиенты банка 25–45 лет",
                12,
                "2026-10-03",
                "2026-10-18",
                "hyp-001",
                "user-002",
            ),
            (
                "res-002",
                "Опрос по заметности категорий кэшбэка",
                "REPORT_READY",
                "QUANTITATIVE",
                "Онлайн-опрос в мобильном приложении",
                "Держатели дебетовых карт",
                350,
                "2026-10-06",
                "2026-10-14",
                "hyp-002",
                "user-002",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO research_designs (id, research_id, goal, questions, success_criteria, user_stories)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "des-001",
                "res-001",
                "Проверить, понимают ли клиенты сокращённую форму заявки",
                "1. Какие поля вызывают вопросы? 2. Сколько времени занимает заполнение?",
                "Не менее 80% респондентов проходят анкету без помощи",
                "Как клиент, я хочу оформить заявку за 2 минуты",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO insights (id, research_id, text, created_by, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("ins-001", "res-001", "8 из 10 участников не понимают, зачем указывать стаж на предпоследнем шаге.", "user-002", "2026-10-09T12:00:00Z"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO research_notes (id, research_id, text, author_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("note-001", "res-001", "Проведено 10 из 12 запланированных интервью.", "user-002", "2026-10-10T16:40:00Z"),
        ],
    )
    conn.commit()
