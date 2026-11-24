"""Конфигурация Product Service."""
from dataclasses import dataclass
from shared.db import get_db_path


@dataclass(frozen=True)
class ProductServiceConfig:
    service_name: str = "product-service"
    db_filename: str = "product.db"

    @property
    def db_path(self):
        return get_db_path(self.db_filename)
