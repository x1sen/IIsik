"""Сервисный слой Notification Service."""
from __future__ import annotations

from datetime import datetime, timezone
import uuid

from services.notification_service.models import NotificationModel
from services.notification_service.repository import NotificationRepository
from shared.exceptions import EntityNotFoundError


class NotificationService:
    def __init__(self, repo: NotificationRepository) -> None:
        self._repo = repo

    def list_notifications(self, user_id: str, unread_only: bool = False) -> list[NotificationModel]:
        return self._repo.list_by_user(user_id=user_id, unread_only=unread_only)

    def create_notification(
        self,
        user_id: str,
        message: str,
        entity_type: str,
        entity_id: str,
        notif_type: str = "IN_APP",
    ) -> NotificationModel:
        item = NotificationModel(
            id=f"ntf-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            type=notif_type,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            is_read=False,
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        return self._repo.create_notification(item)

    def mark_read(self, notification_id: str) -> NotificationModel:
        item = self._repo.mark_read(notification_id)
        if item is None:
            raise EntityNotFoundError("Уведомление", notification_id)
        return item
