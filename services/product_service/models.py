"""Модели Product Service."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProductModel:
    id: str
    name: str
    owner_id: str
    category: str
    status: str
    description: Optional[str]


@dataclass(frozen=True)
class TeamModel:
    id: str
    name: str
    role: str
    product_id: Optional[str]
    member_ids: list[str]
