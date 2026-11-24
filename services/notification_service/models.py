"""Модель Notification Service."""
from dataclasses import dataclass


@dataclass(frozen=True)
class NotificationModel:
    id: str
    user_id: str
    type: str
    message: str
    entity_type: str
    entity_id: str
    is_read: bool
    created_at: str
