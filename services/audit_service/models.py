"""Модель Audit Service."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ActivityLogModel:
    id: str
    entity_type: str
    entity_id: str
    user_id: str
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: str
