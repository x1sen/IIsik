"""Начальные тестовые данные для Hypothesis Service."""

import sqlite3


def seed_hypothesis_db(conn: sqlite3.Connection) -> None:
    cur = conn.execute("SELECT COUNT(*) FROM hypotheses")
    if cur.fetchone()[0] > 0:
        return

    conn.executemany(
        """
        INSERT INTO hypotheses (id, title, description, status, priority, rice_score, product_id, owner_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "hyp-001",
                "Упрощение анкеты онлайн-кредита до 3 шагов",
                "Сокращение количества полей в заявке на онлайн-кредит повысит конверсию оформления.",
                "VALIDATION",
                "P1",
                144.0,
                "prod-001",
                "user-001",
                "2026-10-01T10:00:00Z",
            ),
            (
                "hyp-002",
                "Кэшбэк-подсказки при оплате картой в приложении",
                "Отображение категорий повышенного кэшбэка на главном экране увеличит оборот по картам.",
                "CONFIRMED",
                "P1",
                120.0,
                "prod-002",
                "user-001",
                "2026-10-05T11:30:00Z",
            ),
            (
                "hyp-003",
                "Автозаполнение реквизитов контрагента по УНП в РКО",
                "Подстановка реквизитов снизит время заполнения платёжного поручения для малого бизнеса.",
                "DRAFT",
                "P2",
                64.0,
                "prod-003",
                "user-003",
                "2026-10-12T09:15:00Z",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO hypothesis_templates (id, hypothesis_id, if_action, then_result, because_assumption)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                "tmpl-001",
                "hyp-001",
                "сократить анкету онлайн-кредита с 7 до 3 шагов",
                "конверсия в отправку заявки вырастет на 12%",
                "пользователи бросают оформление на этапе ручного ввода доходов",
            ),
            (
                "tmpl-002",
                "hyp-002",
                "показывать активные категории кэшбэка на экране платежей",
                "транзакционная активность вырастет на 8%",
                "клиенты забывают выбранные категории в начале месяца",
            ),
        ],
    )
    conn.executemany(
        """
        INSERT INTO rice_scores (id, hypothesis_id, reach, impact, confidence, effort, calculated_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("rice-001", "hyp-001", 1200, 1.5, 0.8, 10, 144.0),
            ("rice-002", "hyp-002", 1000, 1.5, 0.8, 10, 120.0),
            ("rice-003", "hyp-003", 400, 1.0, 0.8, 5, 64.0),
        ],
    )
    conn.executemany(
        """
        INSERT INTO comments (id, entity_type, entity_id, author_id, text, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "cmt-001",
                "HYPOTHESIS",
                "hyp-001",
                "user-002",
                "Готовы взять в CX Lab для проведения 10 глубинных интервью.",
                "2026-10-02T14:20:00Z",
            ),
            (
                "cmt-002",
                "HYPOTHESIS",
                "hyp-001",
                "user-001",
                "Отлично, добавил сценарии анкеты во вложения.",
                "2026-10-02T15:05:00Z",
            ),
        ],
    )
    conn.commit()
