"""Конфигурация User Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class UserServiceConfig:
    service_name: str = "user-service"
    db_filename: str = "user.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
