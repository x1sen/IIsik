"""Конфигурация Notification Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class NotificationServiceConfig:
    service_name: str = "notification-service"
    db_filename: str = "notification.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
