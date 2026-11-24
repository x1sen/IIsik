"""Репозиторий Product Service (product.db)."""
from __future__ import annotations
import json
import sqlite3
from typing import Optional
from services.product_service.models import ProductModel, TeamModel


class ProductRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                description TEXT
            );
            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                product_id TEXT,
                member_ids TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            );
            """
        )
        self._conn.commit()

    def get_product(self, product_id: str) -> Optional[ProductModel]:
        row = self._conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return ProductModel(**dict(row)) if row else None

    def list_products(self) -> list[ProductModel]:
        rows = self._conn.execute("SELECT * FROM products").fetchall()
        return [ProductModel(**dict(r)) for r in rows]

    def list_teams(self, product_id: Optional[str] = None) -> list[TeamModel]:
        if product_id:
            rows = self._conn.execute("SELECT * FROM teams WHERE product_id = ?", (product_id,)).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM teams").fetchall()
        return [
            TeamModel(
                id=r["id"],
                name=r["name"],
                role=r["role"],
                product_id=r["product_id"],
                member_ids=json.loads(r["member_ids"]),
            )
            for r in rows
        ]
