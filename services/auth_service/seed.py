"""Начальные учётные записи Auth Service (пароли хранятся только в виде хэшей)."""

import sqlite3

from services.auth_service.service import hash_password


def seed_auth_db(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM auth_users").fetchone()[0] > 0:
        return
    users = [
        ("user-001", "Алексей Смирнов", "smirnov@bank.local", hash_password("pm_pass123"), "PM", "2026-10-01T08:00:00Z"),
        ("user-002", "Елена Кузнецова", "kuznetsova@bank.local", hash_password("cx_pass123"), "CX_EXPERT", "2026-10-01T08:00:00Z"),
        ("user-003", "Дмитрий Волков", "volkov@bank.local", hash_password("agile_pass123"), "AGILE_CENTER", "2026-10-01T08:00:00Z"),
        ("user-004", "Ольга Орлова", "orlova@bank.local", hash_password("admin_pass123"), "ADMIN", "2026-10-01T08:00:00Z"),
    ]
    conn.executemany(
        "INSERT INTO auth_users (id, name, email, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        users,
    )
    conn.commit()
