"""Сервисный слой Idea Portal Service."""
from __future__ import annotations

import uuid

from services.idea_portal_service.models import IdeaModel
from services.idea_portal_service.repository import IdeaPortalRepository
from shared.exceptions import ValidationError


class IdeaPortalService:
    def __init__(self, repo: IdeaPortalRepository) -> None:
        self._repo = repo

    def list_ideas(self) -> list[IdeaModel]:
        return self._repo.list_ideas()

    def submit_idea(
        self,
        product_id: str,
        title: str,
        description: str,
        expected_effect: str,
        category: str,
        author_name: str,
        hypothesis_id: str,
    ) -> IdeaModel:
        if not title.strip() or not description.strip() or not expected_effect.strip():
            raise ValidationError("Заголовок, описание и ожидаемый эффект идеи обязательны")
        idea = IdeaModel(
            id=f"idea-{uuid.uuid4().hex[:8]}",
            product_id=product_id,
            title=title.strip(),
            description=description.strip(),
            expected_effect=expected_effect.strip(),
            category=category.strip() or "Общее направление",
            author_name=author_name.strip() or "Внешний заказчик",
            status="CONVERTED",
            hypothesis_id=hypothesis_id,
        )
        return self._repo.create_idea(idea)
