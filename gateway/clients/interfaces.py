"""Абстрактные интерфейсы клиентов внутренних сервисов (без реального gRPC)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from services.analytics_service.models import DashboardMetricModel
from services.audit_service.models import ActivityLogModel
from services.file_storage_service.models import AttachmentModel
from services.hypothesis_service.models import (
    CommentModel,
    DuplicateCandidateModel,
    HypothesesSummaryModel,
    HypothesisModel,
    HypothesisTemplateModel,
    RICEScoreModel,
)
from services.idea_portal_service.models import IdeaModel
from services.integration_service.models import BacklogTaskModel
from services.notification_service.models import NotificationModel
from services.product_service.models import ProductModel, TeamModel
from services.report_service.models import ReportModel
from services.research_service.models import (
    InsightModel,
    ResearchDesignModel,
    ResearchModel,
    ResearchNoteModel,
)
from services.roadmap_service.models import RoadmapItemModel
from services.user_service.models import UserModel


class HypothesisClient(ABC):
    @abstractmethod
    def get_hypothesis(self, hypothesis_id: str) -> HypothesisModel: ...

    @abstractmethod
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
    ) -> list[HypothesisModel]: ...

    @abstractmethod
    def get_summary(self, product_id: Optional[str] = None) -> HypothesesSummaryModel: ...

    @abstractmethod
    def get_template(self, hypothesis_id: str) -> Optional[HypothesisTemplateModel]: ...

    @abstractmethod
    def get_rice_score(self, hypothesis_id: str) -> Optional[RICEScoreModel]: ...

    @abstractmethod
    def list_comments(self, entity_type: str, entity_id: str) -> list[CommentModel]: ...

    @abstractmethod
    def find_duplicate_hypotheses(
        self, title: str, description: str, product_id: str
    ) -> list[DuplicateCandidateModel]: ...

    @abstractmethod
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
    ) -> HypothesisModel: ...

    @abstractmethod
    def calculate_rice(
        self, hypothesis_id: str, reach: int, impact: float, confidence: float, effort: int
    ) -> RICEScoreModel: ...

    @abstractmethod
    def apply_research_result(self, hypothesis_id: str, target_status: str) -> HypothesisModel: ...

    @abstractmethod
    def begin_export(self, hypothesis_id: str) -> HypothesisModel: ...

    @abstractmethod
    def complete_export(self, hypothesis_id: str) -> HypothesisModel: ...

    @abstractmethod
    def rollback_export(self, hypothesis_id: str) -> HypothesisModel: ...

    @abstractmethod
    def add_comment(
        self, entity_type: str, entity_id: str, author_id: str, text: str
    ) -> CommentModel: ...


class ResearchClient(ABC):
    @abstractmethod
    def get_research(self, research_id: str) -> ResearchModel: ...

    @abstractmethod
    def list_researches(
        self,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        sort_by: str = "start_date",
        sort_dir: str = "DESC",
    ) -> list[ResearchModel]: ...

    @abstractmethod
    def get_design(self, research_id: str) -> Optional[ResearchDesignModel]: ...

    @abstractmethod
    def list_insights(self, research_id: str) -> list[InsightModel]: ...

    @abstractmethod
    def list_notes(self, research_id: str) -> list[ResearchNoteModel]: ...

    @abstractmethod
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
    ) -> ResearchModel: ...

    @abstractmethod
    def add_note(self, research_id: str, author_id: str, text: str) -> ResearchNoteModel: ...

    @abstractmethod
    def add_insight(self, research_id: str, created_by: str, text: str) -> InsightModel: ...

    @abstractmethod
    def complete_research(self, research_id: str) -> ResearchModel: ...

    @abstractmethod
    def mark_completed(self, research_id: str) -> ResearchModel: ...


class ReportClient(ABC):
    @abstractmethod
    def get_report_by_research(self, research_id: str) -> Optional[ReportModel]: ...

    @abstractmethod
    def publish_report(
        self,
        research_id: str,
        conclusion: str,
        recommendations: str,
        file_url: Optional[str] = None,
    ) -> ReportModel: ...


class RoadmapClient(ABC):
    @abstractmethod
    def list_roadmap(self, sort_dir: str = "ASC") -> list[RoadmapItemModel]: ...

    @abstractmethod
    def schedule_item(
        self,
        hypothesis_id: str,
        hypothesis_title: str,
        start_date: str,
        end_date: str,
        dependencies: list[str],
        assignee_id: str,
    ) -> RoadmapItemModel: ...


class AnalyticsClient(ABC):
    @abstractmethod
    def get_dashboard_metrics(
        self, product_id: Optional[str] = None, period: Optional[str] = None
    ) -> list[DashboardMetricModel]: ...


class ProductClient(ABC):
    @abstractmethod
    def get_product(self, product_id: str) -> ProductModel: ...

    @abstractmethod
    def list_products(self) -> list[ProductModel]: ...

    @abstractmethod
    def list_teams(self, product_id: Optional[str] = None) -> list[TeamModel]: ...


class UserClient(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> UserModel: ...

    @abstractmethod
    def list_users(self) -> list[UserModel]: ...

    @abstractmethod
    def check_permission(self, user_id: str, action: str) -> UserModel: ...


class NotificationClient(ABC):
    @abstractmethod
    def list_notifications(self, user_id: str, unread_only: bool = False) -> list[NotificationModel]: ...

    @abstractmethod
    def create_notification(
        self,
        user_id: str,
        message: str,
        entity_type: str,
        entity_id: str,
        notif_type: str = "IN_APP",
    ) -> NotificationModel: ...

    @abstractmethod
    def mark_read(self, notification_id: str) -> NotificationModel: ...


class IdeaPortalClient(ABC):
    @abstractmethod
    def list_ideas(self) -> list[IdeaModel]: ...

    @abstractmethod
    def submit_idea(
        self,
        product_id: str,
        title: str,
        description: str,
        expected_effect: str,
        category: str,
        author_name: str,
        hypothesis_id: str,
    ) -> IdeaModel: ...


class FileStorageClient(ABC):
    @abstractmethod
    def list_attachments(self, entity_type: str, entity_id: str) -> list[AttachmentModel]: ...


class AuditClient(ABC):
    @abstractmethod
    def list_activity_logs(self, entity_type: str, entity_id: str) -> list[ActivityLogModel]: ...

    @abstractmethod
    def record_action(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        action: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> ActivityLogModel: ...


class IntegrationClient(ABC):
    @abstractmethod
    def get_backlog_task(self, hypothesis_id: str) -> Optional[BacklogTaskModel]: ...

    @abstractmethod
    def create_external_task(self, hypothesis_id: str, idempotency_key: str) -> BacklogTaskModel: ...
