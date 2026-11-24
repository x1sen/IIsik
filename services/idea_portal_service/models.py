"""Модель Idea Portal Service."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class IdeaModel:
    id: str
    product_id: str
    title: str
    description: str
    expected_effect: str
    category: str
    author_name: str
    status: str
    hypothesis_id: Optional[str]
