"""Конфигурация File Storage Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class FileStorageServiceConfig:
    service_name: str = "file-storage-service"
    db_filename: str = "file_storage.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
