"""Начальные данные Product Service."""
import json
import sqlite3


def seed_product_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO products (id, name, owner_id, category, status, description) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("prod-001", "Онлайн-кредитование", "user-001", "Кредиты", "ACTIVE", "Оформление потребительских кредитов онлайн"),
            ("prod-002", "Дебетовые карты", "user-001", "Карты", "ACTIVE", "Карточные продукты и программы лояльности"),
            ("prod-003", "РКО для бизнеса", "user-003", "Корпоративный бизнес", "ACTIVE", "Расчётно-кассовое обслуживание МСБ"),
        ],
    )
    conn.executemany(
        "INSERT INTO teams (id, name, role, product_id, member_ids) VALUES (?, ?, ?, ?, ?)",
        [
            ("team-001", "Команда Кредиты Digital", "PRODUCT", "prod-001", json.dumps(["user-001"])),
            ("team-002", "CX Lab", "CX_RESEARCH", "prod-001", json.dumps(["user-002"])),
            ("team-003", "Команда МСБ", "DEV", "prod-003", json.dumps(["user-003"])),
        ],
    )
    conn.commit()
