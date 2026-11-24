"""Начальные данные User Service."""
import sqlite3


def seed_user_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO users (id, name, email, role, team_id, expertise) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("user-001", "Алексей Смирнов", "a.smirnov@bank.local", "PM", "team-001", "Розничное кредитование"),
            ("user-002", "Елена Ковалёва", "e.kovaleva@bank.local", "CX_EXPERT", "team-002", "UX-исследования и интервью"),
            ("user-003", "Дмитрий Орлов", "d.orlov@bank.local", "AGILE_CENTER", "team-003", "Управление портфелем инициатив"),
            ("user-004", "Ирина Волкова", "i.volkova@bank.local", "ADMIN", None, "Администрирование платформы"),
        ],
    )
    conn.commit()
