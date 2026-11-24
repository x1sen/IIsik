"""Сервисный слой Hypothesis Service."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
from typing import Optional
import uuid

from services.hypothesis_service.models import (
    CommentModel,
    DuplicateCandidateModel,
    HypothesesSummaryModel,
    HypothesisModel,
    HypothesisTemplateModel,
    PriorityCountModel,
    RICEScoreModel,
    StatusCountModel,
)
from services.hypothesis_service.repository import HypothesisRepository
from shared.exceptions import BusinessRuleError, EntityNotFoundError, ValidationError


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class HypothesisService:
    def __init__(self, repo: HypothesisRepository) -> None:
        self._repo = repo

    def get_hypothesis(self, hypothesis_id: str) -> HypothesisModel:
        item = self._repo.get_by_id(hypothesis_id)
        if item is None:
            raise EntityNotFoundError("Гипотеза", hypothesis_id)
        return item

    def list_hypotheses(
        self,
        product_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        owner_id: Optional[str] = None,
        min_rice_score: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_dir: str = "DESC",
    ) -> list[HypothesisModel]:
        return self._repo.list_hypotheses(
            product_id=product_id,
            status=status,
            priority=priority,
            owner_id=owner_id,
            min_rice_score=min_rice_score,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def get_summary(self, product_id: Optional[str] = None) -> HypothesesSummaryModel:
        """Агрегация сводных показателей гипотез (по продукту или по всей системе)."""
        items = self._repo.list_hypotheses(product_id=product_id)
        total = len(items)
        status_counts = Counter(h.status for h in items)
        priority_counts = Counter(h.priority for h in items)
        scores = [h.rice_score for h in items if h.rice_score is not None]
        confirmed = status_counts.get("CONFIRMED", 0) + status_counts.get("IN_BACKLOG", 0)
        return HypothesesSummaryModel(
            total_count=total,
            by_status=[StatusCountModel(status=k, count=v) for k, v in sorted(status_counts.items())],
            by_priority=[PriorityCountModel(priority=k, count=v) for k, v in sorted(priority_counts.items())],
            avg_rice_score=round(sum(scores) / len(scores), 2) if scores else None,
            max_rice_score=round(max(scores), 2) if scores else None,
            confirmed_rate=round(confirmed / total, 2) if total else 0.0,
            in_backlog_count=status_counts.get("IN_BACKLOG", 0),
        )

    def create_hypothesis(
        self,
        title: str,
        description: str,
        product_id: str,
        owner_id: str,
        priority: str,
        if_action: str,
        then_result: str,
        because_assumption: str,
    ) -> HypothesisModel:
        if not title.strip() or len(title.strip()) < 3:
            raise ValidationError("Заголовок гипотезы должен содержать минимум 3 символа")
        if not description.strip():
            raise ValidationError("Описание гипотезы не может быть пустым")
        if not if_action.strip() or not then_result.strip() or not because_assumption.strip():
            raise ValidationError("Все блоки шаблона «Если–То–Потому что» обязательны для заполнения")
        if priority not in {"P1", "P2", "P3"}:
            raise ValidationError(f"Недопустимый приоритет '{priority}'")

        hyp_id = f"hyp-{uuid.uuid4().hex[:8]}"
        hypothesis = HypothesisModel(
            id=hyp_id,
            title=title.strip(),
            description=description.strip(),
            status="DRAFT",
            priority=priority,
            rice_score=None,
            product_id=product_id,
            owner_id=owner_id,
            created_at=_now_iso(),
        )
        template = HypothesisTemplateModel(
            id=f"tpl-{uuid.uuid4().hex[:8]}",
            hypothesis_id=hyp_id,
            if_action=if_action.strip(),
            then_result=then_result.strip(),
            because_assumption=because_assumption.strip(),
        )
        return self._repo.create_hypothesis(hypothesis, template)

    def calculate_rice(
        self,
        hypothesis_id: str,
        reach: int,
        impact: float,
        confidence: float,
        effort: int,
    ) -> RICEScoreModel:
        hypothesis = self.get_hypothesis(hypothesis_id)
        if hypothesis.status == "REJECTED":
            raise BusinessRuleError("Нельзя рассчитывать RICE для отклонённой гипотезы")
        if reach <= 0 or effort <= 0 or impact <= 0:
            raise ValidationError("Параметры reach, impact и effort должны быть больше нуля")
        if not (0.0 < confidence <= 1.0):
            raise ValidationError("Параметр confidence должен находиться в диапазоне (0, 1.0]")

        calculated = round((reach * impact * confidence) / effort, 2)
        new_status = "VALIDATION" if hypothesis.status == "DRAFT" else None
        score = RICEScoreModel(
            id=f"rice-{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis_id,
            reach=reach,
            impact=impact,
            confidence=confidence,
            effort=effort,
            calculated_score=calculated,
        )
        return self._repo.save_rice_score(score, new_status=new_status)

    def apply_research_result(self, hypothesis_id: str, target_status: str) -> HypothesisModel:
        if target_status not in {"CONFIRMED", "REJECTED"}:
            raise ValidationError("Целевой статус по итогам исследования должен быть CONFIRMED или REJECTED")
        hypothesis = self.get_hypothesis(hypothesis_id)
        if hypothesis.status in {"EXPORT_PENDING", "IN_BACKLOG"}:
            raise BusinessRuleError("Нельзя изменить статус гипотезы, уже переданной в бэклог")
        return self._repo.update_status(hypothesis_id, target_status)

    def begin_export(self, hypothesis_id: str) -> HypothesisModel:
        hypothesis = self.get_hypothesis(hypothesis_id)
        if hypothesis.status == "IN_BACKLOG":
            raise BusinessRuleError("Гипотеза уже экспортирована в бэклог")
        if hypothesis.status != "CONFIRMED":
            raise BusinessRuleError(
                f"Экспорт в бэклог разрешён только для подтверждённых гипотез (текущий статус: {hypothesis.status})"
            )
        return self._repo.update_status(hypothesis_id, "EXPORT_PENDING")

    def complete_export(self, hypothesis_id: str) -> HypothesisModel:
        return self._repo.update_status(hypothesis_id, "IN_BACKLOG")

    def rollback_export(self, hypothesis_id: str) -> HypothesisModel:
        return self._repo.update_status(hypothesis_id, "CONFIRMED")

    def add_comment(
        self, entity_type: str, entity_id: str, author_id: str, text: str
    ) -> CommentModel:
        if entity_type not in {"HYPOTHESIS", "RESEARCH", "REPORT"}:
            raise ValidationError(f"Недопустимый тип сущности '{entity_type}'")
        if not text.strip():
            raise ValidationError("Текст комментария не может быть пустым")
        comment = CommentModel(
            id=f"cmt-{uuid.uuid4().hex[:8]}",
            entity_type=entity_type,
            entity_id=entity_id,
            author_id=author_id,
            text=text.strip(),
            created_at=_now_iso(),
        )
        return self._repo.add_comment(comment)

    def get_template(self, hypothesis_id: str) -> Optional[HypothesisTemplateModel]:
        return self._repo.get_template_by_hypothesis(hypothesis_id)

    def get_rice_score(self, hypothesis_id: str) -> Optional[RICEScoreModel]:
        return self._repo.get_rice_by_hypothesis(hypothesis_id)

    def list_comments(self, entity_type: str, entity_id: str) -> list[CommentModel]:
        return self._repo.list_comments(entity_type=entity_type, entity_id=entity_id)

    def find_duplicate_hypotheses(
        self, title: str, description: str, product_id: str
    ) -> list[DuplicateCandidateModel]:
        """Полнотекстовый поиск похожих гипотез по совпадению ключевых слов."""
        if not title.strip():
            raise ValidationError("Заголовок для поиска дублей не может быть пустым")

        query_tokens = set(re.findall(r"[а-яА-ЯёЁa-zA-Z0-9]{3,}", f"{title} {description}".lower()))
        if not query_tokens:
            return []

        candidates: list[DuplicateCandidateModel] = []
        for item in self._repo.list_hypotheses(product_id=product_id):
            item_tokens = set(
                re.findall(r"[а-яА-ЯёЁa-zA-Z0-9]{3,}", f"{item.title} {item.description}".lower())
            )
            if not item_tokens:
                continue
            overlap = len(query_tokens & item_tokens)
            similarity = round(overlap / len(query_tokens | item_tokens), 2)
            if similarity >= 0.15:
                candidates.append(
                    DuplicateCandidateModel(
                        hypothesis_id=item.id,
                        title=item.title,
                        similarity=similarity,
                        status=item.status,
                    )
                )
        candidates.sort(key=lambda c: c.similarity, reverse=True)
        return candidates
