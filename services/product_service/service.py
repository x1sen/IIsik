"""Сервисный слой Product Service."""
from typing import Optional
from services.product_service.models import ProductModel, TeamModel
from services.product_service.repository import ProductRepository
from shared.exceptions import EntityNotFoundError


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self._repo = repo

    def get_product(self, product_id: str) -> ProductModel:
        item = self._repo.get_product(product_id)
        if item is None:
            raise EntityNotFoundError("Продукт", product_id)
        return item

    def list_products(self) -> list[ProductModel]:
        return self._repo.list_products()

    def list_teams(self, product_id: Optional[str] = None) -> list[TeamModel]:
        return self._repo.list_teams(product_id=product_id)
