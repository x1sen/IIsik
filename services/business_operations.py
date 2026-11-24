"""Координатор бизнес-операций: синхронные gRPC-вызовы и публикация событий в Kafka."""

from __future__ import annotations

from typing import Optional

from gateway.clients.grpc_clients import ServiceClients
from kafka_layer.events import (
    TOPIC_BACKLOG_TASK_CREATED,
    TOPIC_COMMENT_ADDED,
    TOPIC_HYPOTHESIS_CREATED,
    TOPIC_HYPOTHESIS_EXPORTED,
    TOPIC_HYPOTHESIS_PRIORITIZED,
    TOPIC_HYPOTHESIS_VALIDATED,
    TOPIC_IDEA_SUBMITTED,
    TOPIC_REPORT_READY,
    TOPIC_RESEARCH_COMPLETED,
    TOPIC_RESEARCH_CREATED,
    TOPIC_ROADMAP_ITEM_CREATED,
)
from services.hypothesis_service.models import CommentModel, HypothesisModel, RICEScoreModel
from services.idea_portal_service.models import IdeaModel
from services.integration_service.models import BacklogTaskModel
from services.report_service.models import ReportModel
from services.research_service.models import InsightModel, ResearchModel, ResearchNoteModel
from services.roadmap_service.models import RoadmapItemModel
from shared.exceptions import BusinessRuleError


class BusinessOperations:
    """Реализация сквозных бизнес-сценариев через gRPC-клиенты и Kafka Producer."""

    def __init__(self, clients: ServiceClients) -> None:
        self._clients = clients

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
        self._clients.user.check_permission(owner_id, "CREATE_HYPOTHESIS")
        product = self._clients.product.get_product(product_id)
        hypothesis = self._clients.hypothesis.create_hypothesis(
            title=title,
            description=description,
            product_id=product.id,
            owner_id=owner_id,
            priority=priority,
            if_action=if_action,
            then_result=then_result,
            because_assumption=because_assumption,
        )
        self._clients.kafka_producer.publish(
            TOPIC_HYPOTHESIS_CREATED,
            {
                "hypothesis_id": hypothesis.id,
                "title": hypothesis.title,
                "product_id": product.id,
                "owner_id": owner_id,
                "notify_user_id": product.owner_id,
                "priority": hypothesis.priority,
            },
        )
        return hypothesis

    def calculate_rice(
        self,
        hypothesis_id: str,
        reach: int,
        impact: float,
        confidence: float,
        effort: int,
        user_id: str,
    ) -> RICEScoreModel:
        self._clients.user.check_permission(user_id, "CALCULATE_RICE")
        hypothesis = self._clients.hypothesis.get_hypothesis(hypothesis_id)
        score = self._clients.hypothesis.calculate_rice(
            hypothesis_id=hypothesis_id,
            reach=reach,
            impact=impact,
            confidence=confidence,
            effort=effort,
        )
        self._clients.kafka_producer.publish(
            TOPIC_HYPOTHESIS_PRIORITIZED,
            {
                "hypothesis_id": hypothesis_id,
                "product_id": hypothesis.product_id,
                "priority": hypothesis.priority,
                "rice_score": score.calculated_score,
                "user_id": user_id,
            },
        )
        return score

    def apply_research_result(
        self,
        hypothesis_id: str,
        research_id: str,
        target_status: str,
        user_id: str,
    ) -> HypothesisModel:
        self._clients.user.check_permission(user_id, "APPLY_RESEARCH_RESULT")
        research = self._clients.research.get_research(research_id)
        if research.hypothesis_id != hypothesis_id:
            raise BusinessRuleError(
                f"Исследование '{research_id}' относится к другой гипотезе ('{research.hypothesis_id}')"
            )
        if research.status != "REPORT_READY":
            raise BusinessRuleError(
                f"Нельзя применить результат: исследование '{research_id}' имеет статус '{research.status}', требуется 'REPORT_READY'"
            )
        report = self._clients.report.get_report_by_research(research_id)
        if report is None:
            raise BusinessRuleError(f"Для исследования '{research_id}' не опубликован отчёт")

        old_hyp = self._clients.hypothesis.get_hypothesis(hypothesis_id)
        updated = self._clients.hypothesis.apply_research_result(hypothesis_id, target_status)
        self._clients.research.mark_completed(research_id)
        self._clients.kafka_producer.publish(
            TOPIC_HYPOTHESIS_VALIDATED,
            {
                "hypothesis_id": updated.id,
                "title": updated.title,
                "product_id": updated.product_id,
                "owner_id": updated.owner_id,
                "priority": updated.priority,
                "old_status": old_hyp.status,
                "new_status": updated.status,
                "user_id": user_id,
            },
        )
        return updated

    def export_to_backlog(self, hypothesis_id: str, user_id: str) -> BacklogTaskModel:
        self._clients.user.check_permission(user_id, "EXPORT_TO_BACKLOG")
        hypothesis = self._clients.hypothesis.begin_export(hypothesis_id)
        try:
            task = self._clients.integration.create_external_task(
                hypothesis_id=hypothesis.id, idempotency_key=hypothesis.id
            )
        except Exception:
            self._clients.hypothesis.rollback_export(hypothesis_id)
            raise
        self._clients.hypothesis.complete_export(hypothesis_id)
        self._clients.kafka_producer.publish(
            TOPIC_BACKLOG_TASK_CREATED,
            {
                "backlog_task_id": task.id,
                "hypothesis_id": hypothesis.id,
                "title": hypothesis.title,
                "product_id": hypothesis.product_id,
                "owner_id": hypothesis.owner_id,
                "external_key": task.external_key,
                "external_url": task.external_url,
            },
        )
        self._clients.kafka_producer.publish(
            TOPIC_HYPOTHESIS_EXPORTED,
            {
                "hypothesis_id": hypothesis.id,
                "product_id": hypothesis.product_id,
                "owner_id": hypothesis.owner_id,
                "external_key": task.external_key,
                "exported_by": user_id,
            },
        )
        return task

    def create_research(
        self,
        hypothesis_id: str,
        title: str,
        research_type: str,
        method: str,
        target_audience: str,
        sample_size: int,
        assignee_id: str,
        goal: str,
        questions: str,
        success_criteria: str,
        user_stories: Optional[str] = None,
    ) -> ResearchModel:
        hypothesis = self._clients.hypothesis.get_hypothesis(hypothesis_id)
        self._clients.user.check_permission(assignee_id, "CREATE_RESEARCH")
        research = self._clients.research.create_research(
            hypothesis_id=hypothesis_id,
            title=title,
            research_type=research_type,
            method=method,
            target_audience=target_audience,
            sample_size=sample_size,
            assignee_id=assignee_id,
            goal=goal,
            questions=questions,
            success_criteria=success_criteria,
            user_stories=user_stories,
        )
        self._clients.kafka_producer.publish(
            TOPIC_RESEARCH_CREATED,
            {
                "research_id": research.id,
                "title": research.title,
                "hypothesis_id": hypothesis.id,
                "product_id": hypothesis.product_id,
                "assignee_id": assignee_id,
            },
        )
        return research

    def add_research_note(self, research_id: str, author_id: str, text: str) -> ResearchNoteModel:
        self._clients.user.get_user(author_id)
        return self._clients.research.add_note(research_id, author_id, text)

    def add_insight(self, research_id: str, created_by: str, text: str) -> InsightModel:
        self._clients.user.get_user(created_by)
        return self._clients.research.add_insight(research_id, created_by, text)

    def publish_report(
        self,
        research_id: str,
        conclusion: str,
        recommendations: str,
        file_url: Optional[str],
        author_id: str,
    ) -> ReportModel:
        self._clients.user.check_permission(author_id, "PUBLISH_REPORT")
        research = self._clients.research.get_research(research_id)
        report = self._clients.report.publish_report(
            research_id=research_id,
            conclusion=conclusion,
            recommendations=recommendations,
            file_url=file_url,
        )
        self._clients.research.complete_research(research_id)
        hypothesis = self._clients.hypothesis.get_hypothesis(research.hypothesis_id)
        self._clients.kafka_producer.publish(
            TOPIC_RESEARCH_COMPLETED,
            {
                "research_id": research.id,
                "hypothesis_id": hypothesis.id,
                "product_id": hypothesis.product_id,
                "report_id": report.id,
                "conclusion": report.conclusion,
                "author_id": author_id,
            },
        )
        self._clients.kafka_producer.publish(
            TOPIC_REPORT_READY,
            {
                "report_id": report.id,
                "research_id": research.id,
                "research_title": research.title,
                "hypothesis_id": hypothesis.id,
                "product_id": hypothesis.product_id,
                "owner_id": hypothesis.owner_id,
                "conclusion": report.conclusion,
                "author_id": author_id,
            },
        )
        return report

    def schedule_on_roadmap(
        self,
        hypothesis_id: str,
        start_date: str,
        end_date: str,
        dependencies: list[str],
        assignee_id: str,
    ) -> RoadmapItemModel:
        hypothesis = self._clients.hypothesis.get_hypothesis(hypothesis_id)
        self._clients.user.get_user(assignee_id)
        item = self._clients.roadmap.schedule_item(
            hypothesis_id=hypothesis.id,
            hypothesis_title=hypothesis.title,
            start_date=start_date,
            end_date=end_date,
            dependencies=dependencies,
            assignee_id=assignee_id,
        )
        self._clients.kafka_producer.publish(
            TOPIC_ROADMAP_ITEM_CREATED,
            {
                "roadmap_item_id": item.id,
                "hypothesis_id": hypothesis.id,
                "title": hypothesis.title,
                "product_id": hypothesis.product_id,
                "start_date": start_date,
                "end_date": end_date,
                "assignee_id": assignee_id,
            },
        )
        return item

    def submit_idea(
        self,
        product_id: str,
        title: str,
        description: str,
        expected_effect: str,
        category: str,
        author_name: str,
        priority: str = "P2",
        owner_id: Optional[str] = None,
        if_action: Optional[str] = None,
        then_result: Optional[str] = None,
        because_assumption: Optional[str] = None,
    ) -> IdeaModel:
        product = self._clients.product.get_product(product_id)
        resolved_owner = owner_id or product.owner_id
        self._clients.user.get_user(resolved_owner)
        hypothesis = self._clients.hypothesis.create_hypothesis(
            title=title,
            description=description,
            product_id=product.id,
            owner_id=resolved_owner,
            priority=priority,
            if_action=(if_action or description).strip(),
            then_result=(then_result or expected_effect).strip(),
            because_assumption=(because_assumption or f"Инициатива от: {author_name} ({category})").strip(),
        )
        idea = self._clients.idea_portal.submit_idea(
            product_id=product.id,
            title=title,
            description=description,
            expected_effect=expected_effect,
            category=category,
            author_name=author_name,
            hypothesis_id=hypothesis.id,
        )
        self._clients.kafka_producer.publish(
            TOPIC_IDEA_SUBMITTED,
            {
                "idea_id": idea.id,
                "title": idea.title,
                "hypothesis_id": hypothesis.id,
                "product_id": product.id,
                "owner_id": resolved_owner,
                "notify_user_id": product.owner_id,
            },
        )
        return idea

    def add_comment(
        self, entity_type: str, entity_id: str, author_id: str, text: str
    ) -> CommentModel:
        self._clients.user.check_permission(author_id, "ADD_COMMENT")
        comment = self._clients.hypothesis.add_comment(
            entity_type=entity_type, entity_id=entity_id, author_id=author_id, text=text
        )
        self._clients.kafka_producer.publish(
            TOPIC_COMMENT_ADDED,
            {
                "comment_id": comment.id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "author_id": author_id,
            },
        )
        return comment
