"""Mock-реализации клиентов внутренних сервисов (без сетевых gRPC-вызовов)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gateway.clients.interfaces import (
    AnalyticsClient,
    AuditClient,
    AuthClient,
    FileStorageClient,
    HypothesisClient,
    IdeaPortalClient,
    IntegrationClient,
    NotificationClient,
    ProductClient,
    ReportClient,
    ResearchClient,
    RoadmapClient,
    UserClient,
)
from services.analytics_service.config import AnalyticsServiceConfig
from services.analytics_service.repository import AnalyticsRepository
from services.analytics_service.seed import seed_analytics_db
from services.analytics_service.service import AnalyticsService
from services.audit_service.config import AuditServiceConfig
from services.audit_service.repository import AuditRepository
from services.audit_service.seed import seed_audit_db
from services.audit_service.service import AuditService
from services.auth_service.config import AuthServiceConfig
from services.auth_service.repository import AuthRepository
from services.auth_service.seed import seed_auth_db
from services.auth_service.service import AuthService
from services.auth_service.session_store import RedisSessionStore, create_redis_client
from services.file_storage_service.config import FileStorageServiceConfig
from services.file_storage_service.repository import FileStorageRepository
from services.file_storage_service.seed import seed_file_storage_db
from services.file_storage_service.service import FileStorageService
from services.hypothesis_service.config import HypothesisServiceConfig
from services.hypothesis_service.repository import HypothesisRepository
from services.hypothesis_service.seed import seed_hypothesis_db
from services.hypothesis_service.service import HypothesisService
from services.idea_portal_service.config import IdeaPortalServiceConfig
from services.idea_portal_service.repository import IdeaPortalRepository
from services.idea_portal_service.seed import seed_idea_db
from services.idea_portal_service.service import IdeaPortalService
from services.integration_service.config import IntegrationServiceConfig
from services.integration_service.repository import IntegrationRepository
from services.integration_service.seed import seed_integration_db
from services.integration_service.service import IntegrationService
from services.notification_service.config import NotificationServiceConfig
from services.notification_service.repository import NotificationRepository
from services.notification_service.seed import seed_notification_db
from services.notification_service.service import NotificationService
from services.product_service.config import ProductServiceConfig
from services.product_service.repository import ProductRepository
from services.product_service.seed import seed_product_db
from services.product_service.service import ProductService
from services.report_service.config import ReportServiceConfig
from services.report_service.repository import ReportRepository
from services.report_service.seed import seed_report_db
from services.report_service.service import ReportService
from services.research_service.config import ResearchServiceConfig
from services.research_service.repository import ResearchRepository
from services.research_service.seed import seed_research_db
from services.research_service.service import ResearchService
from services.roadmap_service.config import RoadmapServiceConfig
from services.roadmap_service.repository import RoadmapRepository
from services.roadmap_service.seed import seed_roadmap_db
from services.roadmap_service.service import RoadmapService
from services.user_service.config import UserServiceConfig
from services.user_service.repository import UserRepository
from services.user_service.seed import seed_user_db
from services.user_service.service import UserService
from shared.db import connect_sqlite


class MockHypothesisClient(HypothesisClient):
    """Заглушка gRPC-клиента HypothesisService (in-process вызов без сети)."""

    def __init__(self, svc: HypothesisService) -> None:
        self._svc = svc

    def get_hypothesis(self, hypothesis_id: str):
        return self._svc.get_hypothesis(hypothesis_id)

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
    ):
        return self._svc.list_hypotheses(
            product_id=product_id,
            status=status,
            priority=priority,
            owner_id=owner_id,
            min_rice_score=min_rice_score,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def get_summary(self, product_id: Optional[str] = None):
        return self._svc.get_summary(product_id=product_id)

    def get_template(self, hypothesis_id: str):
        return self._svc.get_template(hypothesis_id)

    def get_rice_score(self, hypothesis_id: str):
        return self._svc.get_rice_score(hypothesis_id)

    def list_comments(self, entity_type: str, entity_id: str):
        return self._svc.list_comments(entity_type, entity_id)

    def find_duplicate_hypotheses(self, title: str, description: str, product_id: str):
        return self._svc.find_duplicate_hypotheses(title, description, product_id)

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
    ):
        return self._svc.create_hypothesis(
            title=title,
            description=description,
            product_id=product_id,
            owner_id=owner_id,
            priority=priority,
            if_action=if_action,
            then_result=then_result,
            because_assumption=because_assumption,
        )

    def calculate_rice(
        self, hypothesis_id: str, reach: int, impact: float, confidence: float, effort: int
    ):
        return self._svc.calculate_rice(hypothesis_id, reach, impact, confidence, effort)

    def apply_research_result(self, hypothesis_id: str, target_status: str):
        return self._svc.apply_research_result(hypothesis_id, target_status)

    def begin_export(self, hypothesis_id: str):
        return self._svc.begin_export(hypothesis_id)

    def complete_export(self, hypothesis_id: str):
        return self._svc.complete_export(hypothesis_id)

    def rollback_export(self, hypothesis_id: str):
        return self._svc.rollback_export(hypothesis_id)

    def add_comment(self, entity_type: str, entity_id: str, author_id: str, text: str):
        return self._svc.add_comment(entity_type, entity_id, author_id, text)


class MockResearchClient(ResearchClient):
    def __init__(self, svc: ResearchService) -> None:
        self._svc = svc

    def get_research(self, research_id: str):
        return self._svc.get_research(research_id)

    def list_researches(
        self,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        sort_by: str = "start_date",
        sort_dir: str = "DESC",
    ):
        return self._svc.list_researches(
            hypothesis_id=hypothesis_id,
            status=status,
            assignee_id=assignee_id,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def get_design(self, research_id: str):
        return self._svc.get_design(research_id)

    def list_insights(self, research_id: str):
        return self._svc.list_insights(research_id)

    def list_notes(self, research_id: str):
        return self._svc.list_notes(research_id)

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
    ):
        return self._svc.create_research(
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

    def add_note(self, research_id: str, author_id: str, text: str):
        return self._svc.add_note(research_id, author_id, text)

    def add_insight(self, research_id: str, created_by: str, text: str):
        return self._svc.add_insight(research_id, created_by, text)

    def complete_research(self, research_id: str):
        return self._svc.complete_research(research_id)

    def mark_completed(self, research_id: str):
        return self._svc.mark_completed(research_id)


class MockReportClient(ReportClient):
    def __init__(self, svc: ReportService) -> None:
        self._svc = svc

    def get_report_by_research(self, research_id: str):
        return self._svc.get_report_by_research(research_id)

    def publish_report(
        self,
        research_id: str,
        conclusion: str,
        recommendations: str,
        file_url: Optional[str] = None,
    ):
        return self._svc.publish_report(
            research_id=research_id,
            conclusion=conclusion,
            recommendations=recommendations,
            file_url=file_url,
        )


class MockRoadmapClient(RoadmapClient):
    def __init__(self, svc: RoadmapService) -> None:
        self._svc = svc

    def list_roadmap(self, sort_dir: str = "ASC"):
        return self._svc.list_roadmap(sort_dir=sort_dir)

    def schedule_item(
        self,
        hypothesis_id: str,
        hypothesis_title: str,
        start_date: str,
        end_date: str,
        dependencies: list[str],
        assignee_id: str,
    ):
        return self._svc.schedule_item(
            hypothesis_id=hypothesis_id,
            hypothesis_title=hypothesis_title,
            start_date=start_date,
            end_date=end_date,
            dependencies=dependencies,
            assignee_id=assignee_id,
        )


class MockAnalyticsClient(AnalyticsClient):
    def __init__(self, svc: AnalyticsService) -> None:
        self._svc = svc

    def get_dashboard_metrics(self, product_id: Optional[str] = None, period: Optional[str] = None):
        return self._svc.get_dashboard_metrics(product_id=product_id, period=period)


class MockProductClient(ProductClient):
    def __init__(self, svc: ProductService) -> None:
        self._svc = svc

    def get_product(self, product_id: str):
        return self._svc.get_product(product_id)

    def list_products(self):
        return self._svc.list_products()

    def list_teams(self, product_id: Optional[str] = None):
        return self._svc.list_teams(product_id=product_id)


class MockUserClient(UserClient):
    def __init__(self, svc: UserService) -> None:
        self._svc = svc

    def get_user(self, user_id: str):
        return self._svc.get_user(user_id)

    def list_users(self):
        return self._svc.list_users()

    def check_permission(self, user_id: str, action: str):
        return self._svc.check_permission(user_id, action)


class MockNotificationClient(NotificationClient):
    def __init__(self, svc: NotificationService) -> None:
        self._svc = svc

    def list_notifications(self, user_id: str, unread_only: bool = False):
        return self._svc.list_notifications(user_id=user_id, unread_only=unread_only)

    def create_notification(
        self,
        user_id: str,
        message: str,
        entity_type: str,
        entity_id: str,
        notif_type: str = "IN_APP",
    ):
        return self._svc.create_notification(
            user_id=user_id,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            notif_type=notif_type,
        )

    def mark_read(self, notification_id: str):
        return self._svc.mark_read(notification_id)


class MockIdeaPortalClient(IdeaPortalClient):
    def __init__(self, svc: IdeaPortalService) -> None:
        self._svc = svc

    def list_ideas(self):
        return self._svc.list_ideas()

    def submit_idea(
        self,
        product_id: str,
        title: str,
        description: str,
        expected_effect: str,
        category: str,
        author_name: str,
        hypothesis_id: str,
    ):
        return self._svc.submit_idea(
            product_id=product_id,
            title=title,
            description=description,
            expected_effect=expected_effect,
            category=category,
            author_name=author_name,
            hypothesis_id=hypothesis_id,
        )


class MockFileStorageClient(FileStorageClient):
    def __init__(self, svc: FileStorageService) -> None:
        self._svc = svc

    def list_attachments(self, entity_type: str, entity_id: str):
        return self._svc.list_attachments(entity_type=entity_type, entity_id=entity_id)


class MockAuditClient(AuditClient):
    def __init__(self, svc: AuditService) -> None:
        self._svc = svc

    def list_activity_logs(self, entity_type: str, entity_id: str):
        return self._svc.list_activity_logs(entity_type=entity_type, entity_id=entity_id)

    def record_action(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        action: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ):
        return self._svc.record_action(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )


class MockIntegrationClient(IntegrationClient):
    def __init__(self, svc: IntegrationService) -> None:
        self._svc = svc

    def get_backlog_task(self, hypothesis_id: str):
        return self._svc.get_backlog_task(hypothesis_id)

    def create_external_task(self, hypothesis_id: str, idempotency_key: str):
        return self._svc.create_external_task(hypothesis_id, idempotency_key)


class MockAuthClient(AuthClient):
    def __init__(self, svc: AuthService) -> None:
        self._svc = svc

    def register(self, name: str, email: str, password: str, role: str = "PM"):
        return self._svc.register(name=name, email=email, password=password, role=role)

    def login(self, email: str, password: str):
        return self._svc.login(email=email, password=password)

    def verify_token_and_session(self, token: str):
        return self._svc.verify_token_and_session(token=token)

    def logout(self, token: str):
        return self._svc.logout(token=token)


@dataclass(frozen=True)
class ServiceClients:
    hypothesis: HypothesisClient
    research: ResearchClient
    report: ReportClient
    roadmap: RoadmapClient
    analytics: AnalyticsClient
    product: ProductClient
    user: UserClient
    notification: NotificationClient
    idea_portal: IdeaPortalClient
    file_storage: FileStorageClient
    audit: AuditClient
    integration: IntegrationClient
    auth: AuthClient
    auth_service: AuthService


def build_mock_clients(
    redis_client=None, session_ttl_seconds: Optional[int] = None
) -> ServiceClients:
    """Инициализирует изолированные БД всех сервисов, Redis-хранилище сессий и mock-клиенты."""
    h_conn = connect_sqlite(HypothesisServiceConfig().db_path)
    h_repo = HypothesisRepository(h_conn)
    seed_hypothesis_db(h_conn)

    r_conn = connect_sqlite(ResearchServiceConfig().db_path)
    r_repo = ResearchRepository(r_conn)
    seed_research_db(r_conn)

    rep_conn = connect_sqlite(ReportServiceConfig().db_path)
    rep_repo = ReportRepository(rep_conn)
    seed_report_db(rep_conn)

    road_conn = connect_sqlite(RoadmapServiceConfig().db_path)
    road_repo = RoadmapRepository(road_conn)
    seed_roadmap_db(road_conn)

    ana_conn = connect_sqlite(AnalyticsServiceConfig().db_path)
    ana_repo = AnalyticsRepository(ana_conn)
    seed_analytics_db(ana_conn)

    prod_conn = connect_sqlite(ProductServiceConfig().db_path)
    prod_repo = ProductRepository(prod_conn)
    seed_product_db(prod_conn)

    usr_conn = connect_sqlite(UserServiceConfig().db_path)
    usr_repo = UserRepository(usr_conn)
    seed_user_db(usr_conn)

    not_conn = connect_sqlite(NotificationServiceConfig().db_path)
    not_repo = NotificationRepository(not_conn)
    seed_notification_db(not_conn)

    idea_conn = connect_sqlite(IdeaPortalServiceConfig().db_path)
    idea_repo = IdeaPortalRepository(idea_conn)
    seed_idea_db(idea_conn)

    fs_conn = connect_sqlite(FileStorageServiceConfig().db_path)
    fs_repo = FileStorageRepository(fs_conn)
    seed_file_storage_db(fs_conn)

    aud_conn = connect_sqlite(AuditServiceConfig().db_path)
    aud_repo = AuditRepository(aud_conn)
    seed_audit_db(aud_conn)

    intg_conn = connect_sqlite(IntegrationServiceConfig().db_path)
    intg_repo = IntegrationRepository(intg_conn)
    seed_integration_db(intg_conn)

    auth_cfg = AuthServiceConfig(
        session_ttl_seconds=session_ttl_seconds
        if session_ttl_seconds is not None
        else AuthServiceConfig().session_ttl_seconds
    )
    auth_conn = connect_sqlite(auth_cfg.db_filename)
    auth_repo = AuthRepository(auth_conn)
    seed_auth_db(auth_conn)
    r_client = redis_client if redis_client is not None else create_redis_client(auth_cfg.redis_url)
    session_store = RedisSessionStore(r_client)
    auth_svc = AuthService(auth_repo, session_store, config=auth_cfg)

    return ServiceClients(
        hypothesis=MockHypothesisClient(HypothesisService(h_repo)),
        research=MockResearchClient(ResearchService(r_repo)),
        report=MockReportClient(ReportService(rep_repo)),
        roadmap=MockRoadmapClient(RoadmapService(road_repo)),
        analytics=MockAnalyticsClient(AnalyticsService(ana_repo)),
        product=MockProductClient(ProductService(prod_repo)),
        user=MockUserClient(UserService(usr_repo)),
        notification=MockNotificationClient(NotificationService(not_repo)),
        idea_portal=MockIdeaPortalClient(IdeaPortalService(idea_repo)),
        file_storage=MockFileStorageClient(FileStorageService(fs_repo)),
        audit=MockAuditClient(AuditService(aud_repo)),
        integration=MockIntegrationClient(IntegrationService(intg_repo)),
        auth=MockAuthClient(auth_svc),
        auth_service=auth_svc,
    )
