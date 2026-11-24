"""Изолированный помощник подключения к SQLite (Database per Service)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_db_path(db_filename: str) -> Path:
    base_dir = Path(os.environ.get("PDP_DATA_DIR", str(DEFAULT_DATA_DIR)))
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / db_filename


def connect_sqlite(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
