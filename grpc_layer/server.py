"""gRPC-сервер всех внутренних микросервисов системы."""

from __future__ import annotations

from concurrent import futures
from dataclasses import dataclass
from typing import Any, Optional

import grpc

from grpc_layer.converters import (
    backlog_to_proto,
    grpc_error_guard,
    hyp_to_proto,
    report_to_proto,
    res_to_proto,
    rice_to_proto,
)
from protos import platform_pb2, platform_pb2_grpc
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
from shared.db import connect_sqlite, get_db_path


@dataclass(frozen=True)
class ServiceRegistry:
    hypothesis: HypothesisService
    research: ResearchService
    report: ReportService
    roadmap: RoadmapService
    analytics: AnalyticsService
    product: ProductService
    user: UserService
    notification: NotificationService
    idea_portal: IdeaPortalService
    file_storage: FileStorageService
    audit: AuditService
    integration: IntegrationService
    auth: AuthService
    redis_client: Any


class HypothesisServicer(platform_pb2_grpc.HypothesisServiceServicer):
    def __init__(self, svc: HypothesisService) -> None:
        self._svc = svc

    @grpc_error_guard
    def GetHypothesis(self, request, context):
        return hyp_to_proto(self._svc.get_hypothesis(request.hypothesis_id))

    @grpc_error_guard
    def ListHypotheses(self, request, context):
        items = self._svc.list_hypotheses(
            product_id=request.product_id or None,
            status=request.status or None,
            priority=request.priority or None,
            owner_id=request.owner_id or None,
            min_rice_score=request.min_rice_score if request.has_min_rice_score else None,
            search=request.search or None,
            sort_by=request.sort_by or "created_at",
            sort_dir=request.sort_dir or "DESC",
        )
        return platform_pb2.HypothesisListProto(items=[hyp_to_proto(h) for h in items])

    @grpc_error_guard
    def GetSummary(self, request, context):
        s = self._svc.get_summary(product_id=request.product_id or None)
        return platform_pb2.HypothesesSummaryProto(
            total_count=s.total_count,
            by_status=[
                platform_pb2.StatusCountProto(status=x.status, count=x.count) for x in s.by_status
            ],
            by_priority=[
                platform_pb2.PriorityCountProto(priority=x.priority, count=x.count)
                for x in s.by_priority
            ],
            has_avg_rice_score=s.avg_rice_score is not None,
            avg_rice_score=s.avg_rice_score or 0.0,
            has_max_rice_score=s.max_rice_score is not None,
            max_rice_score=s.max_rice_score or 0.0,
            confirmed_rate=s.confirmed_rate,
            in_backlog_count=s.in_backlog_count,
        )

    @grpc_error_guard
    def GetTemplate(self, request, context):
        t = self._svc.get_template(request.hypothesis_id)
        if t is None:
            return platform_pb2.HypothesisTemplateProto(found=False)
        return platform_pb2.HypothesisTemplateProto(
            found=True,
            id=t.id,
            hypothesis_id=t.hypothesis_id,
            if_action=t.if_action,
            then_result=t.then_result,
            because_assumption=t.because_assumption,
        )

    @grpc_error_guard
    def GetRiceScore(self, request, context):
        return rice_to_proto(self._svc.get_rice_score(request.hypothesis_id))

    @grpc_error_guard
    def ListComments(self, request, context):
        items = self._svc.list_comments(request.entity_type, request.entity_id)
        return platform_pb2.CommentListProto(
            items=[
                platform_pb2.CommentProto(
                    id=c.id,
                    entity_type=c.entity_type,
                    entity_id=c.entity_id,
                    author_id=c.author_id,
                    text=c.text,
                    created_at=c.created_at,
                )
                for c in items
            ]
        )

    @grpc_error_guard
    def FindDuplicateHypotheses(self, request, context):
        items = self._svc.find_duplicate_hypotheses(
            request.title, request.description, request.product_id
        )
        return platform_pb2.DuplicateListProto(
            items=[
                platform_pb2.DuplicateCandidateProto(
                    hypothesis_id=c.hypothesis_id,
                    title=c.title,
                    similarity=c.similarity,
                    status=c.status,
                )
                for c in items
            ]
        )

    @grpc_error_guard
    def CreateHypothesis(self, request, context):
        h = self._svc.create_hypothesis(
            title=request.title,
            description=request.description,
            product_id=request.product_id,
            owner_id=request.owner_id,
            priority=request.priority,
            if_action=request.if_action,
            then_result=request.then_result,
            because_assumption=request.because_assumption,
        )
        return hyp_to_proto(h)

    @grpc_error_guard
    def CalculateRICE(self, request, context):
        s = self._svc.calculate_rice(
            hypothesis_id=request.hypothesis_id,
            reach=request.reach,
            impact=request.impact,
            confidence=request.confidence,
            effort=request.effort,
        )
        return rice_to_proto(s)

    @grpc_error_guard
    def ApplyResearchResult(self, request, context):
        return hyp_to_proto(
            self._svc.apply_research_result(request.hypothesis_id, request.target_status)
        )

    @grpc_error_guard
    def BeginExport(self, request, context):
        return hyp_to_proto(self._svc.begin_export(request.hypothesis_id))

    @grpc_error_guard
    def CompleteExport(self, request, context):
        return hyp_to_proto(self._svc.complete_export(request.hypothesis_id))

    @grpc_error_guard
    def RollbackExport(self, request, context):
        return hyp_to_proto(self._svc.rollback_export(request.hypothesis_id))

    @grpc_error_guard
    def AddComment(self, request, context):
        c = self._svc.add_comment(
            request.entity_type, request.entity_id, request.author_id, request.text
        )
        return platform_pb2.CommentProto(
            id=c.id,
            entity_type=c.entity_type,
            entity_id=c.entity_id,
            author_id=c.author_id,
            text=c.text,
            created_at=c.created_at,
        )


class ResearchServicer(platform_pb2_grpc.ResearchServiceServicer):
    def __init__(self, svc: ResearchService) -> None:
        self._svc = svc

    @grpc_error_guard
    def GetResearch(self, request, context):
        return res_to_proto(self._svc.get_research(request.research_id))

    @grpc_error_guard
    def ListResearches(self, request, context):
        items = self._svc.list_researches(
            hypothesis_id=request.hypothesis_id or None,
            status=request.status or None,
            assignee_id=request.assignee_id or None,
            sort_by=request.sort_by or "start_date",
            sort_dir=request.sort_dir or "DESC",
        )
        return platform_pb2.ResearchListProto(items=[res_to_proto(r) for r in items])

    @grpc_error_guard
    def GetDesign(self, request, context):
        d = self._svc.get_design(request.research_id)
        if d is None:
            return platform_pb2.ResearchDesignProto(found=False)
        return platform_pb2.ResearchDesignProto(
            found=True,
            id=d.id,
            research_id=d.research_id,
            goal=d.goal,
            questions=d.questions,
            success_criteria=d.success_criteria,
            user_stories=d.user_stories or "",
        )

    @grpc_error_guard
    def ListInsights(self, request, context):
        items = self._svc.list_insights(request.research_id)
        return platform_pb2.InsightListProto(
            items=[
                platform_pb2.InsightProto(
                    id=i.id,
                    research_id=i.research_id,
                    text=i.text,
                    created_by=i.created_by,
                    created_at=i.created_at,
                )
                for i in items
            ]
        )

    @grpc_error_guard
    def ListNotes(self, request, context):
        items = self._svc.list_notes(request.research_id)
        return platform_pb2.ResearchNoteListProto(
            items=[
                platform_pb2.ResearchNoteProto(
                    id=n.id,
                    research_id=n.research_id,
                    text=n.text,
                    author_id=n.author_id,
                    created_at=n.created_at,
                )
                for n in items
            ]
        )

    @grpc_error_guard
    def CreateResearch(self, request, context):
        r = self._svc.create_research(
            hypothesis_id=request.hypothesis_id,
            title=request.title,
            research_type=request.research_type,
            method=request.method,
            target_audience=request.target_audience,
            sample_size=request.sample_size,
            assignee_id=request.assignee_id,
            goal=request.goal,
            questions=request.questions,
            success_criteria=request.success_criteria,
            user_stories=request.user_stories or None,
        )
        return res_to_proto(r)

    @grpc_error_guard
    def AddNote(self, request, context):
        n = self._svc.add_note(request.research_id, request.user_id, request.text)
        return platform_pb2.ResearchNoteProto(
            id=n.id,
            research_id=n.research_id,
            text=n.text,
            author_id=n.author_id,
            created_at=n.created_at,
        )

    @grpc_error_guard
    def AddInsight(self, request, context):
        i = self._svc.add_insight(request.research_id, request.user_id, request.text)
        return platform_pb2.InsightProto(
            id=i.id,
            research_id=i.research_id,
            text=i.text,
            created_by=i.created_by,
            created_at=i.created_at,
        )

    @grpc_error_guard
    def CompleteResearch(self, request, context):
        return res_to_proto(self._svc.complete_research(request.research_id))

    @grpc_error_guard
    def MarkCompleted(self, request, context):
        return res_to_proto(self._svc.mark_completed(request.research_id))


class ReportServicer(platform_pb2_grpc.ReportServiceServicer):
    def __init__(self, svc: ReportService) -> None:
        self._svc = svc

    @grpc_error_guard
    def GetReportByResearch(self, request, context):
        return report_to_proto(self._svc.get_report_by_research(request.research_id))

    @grpc_error_guard
    def PublishReport(self, request, context):
        rep = self._svc.publish_report(
            research_id=request.research_id,
            conclusion=request.conclusion,
            recommendations=request.recommendations,
            file_url=request.file_url or None,
        )
        return report_to_proto(rep)


class RoadmapServicer(platform_pb2_grpc.RoadmapServiceServicer):
    def __init__(self, svc: RoadmapService) -> None:
        self._svc = svc

    @grpc_error_guard
    def ListRoadmap(self, request, context):
        items = self._svc.list_roadmap(sort_dir=request.sort_dir or "ASC")
        return platform_pb2.RoadmapListProto(
            items=[
                platform_pb2.RoadmapItemProto(
                    id=i.id,
                    hypothesis_id=i.hypothesis_id,
                    hypothesis_title=i.hypothesis_title,
                    start_date=i.start_date,
                    end_date=i.end_date,
                    duration=i.duration,
                    dependencies=i.dependencies,
                    assignee_id=i.assignee_id,
                )
                for i in items
            ]
        )

    @grpc_error_guard
    def ScheduleItem(self, request, context):
        i = self._svc.schedule_item(
            hypothesis_id=request.hypothesis_id,
            hypothesis_title=request.hypothesis_title,
            start_date=request.start_date,
            end_date=request.end_date,
            dependencies=list(request.dependencies),
            assignee_id=request.assignee_id,
        )
        return platform_pb2.RoadmapItemProto(
            id=i.id,
            hypothesis_id=i.hypothesis_id,
            hypothesis_title=i.hypothesis_title,
            start_date=i.start_date,
            end_date=i.end_date,
            duration=i.duration,
            dependencies=i.dependencies,
            assignee_id=i.assignee_id,
        )


class AnalyticsServicer(platform_pb2_grpc.AnalyticsServiceServicer):
    def __init__(self, svc: AnalyticsService) -> None:
        self._svc = svc

    @grpc_error_guard
    def GetDashboardMetrics(self, request, context):
        items = self._svc.get_dashboard_metrics(
            product_id=request.product_id or None, period=request.period or None
        )
        return platform_pb2.DashboardMetricsListProto(
            items=[
                platform_pb2.DashboardMetricProto(
                    id=m.id,
                    metric_type=m.metric_type,
                    product_id=m.product_id,
                    period=m.period,
                    value=m.value,
                )
                for m in items
            ]
        )


class ProductServicer(platform_pb2_grpc.ProductServiceServicer):
    def __init__(self, svc: ProductService) -> None:
        self._svc = svc

    @grpc_error_guard
    def GetProduct(self, request, context):
        p = self._svc.get_product(request.product_id)
        return platform_pb2.ProductProto(
            id=p.id,
            name=p.name,
            category=p.category,
            status=p.status,
            description=p.description or "",
            owner_id=p.owner_id,
        )

    @grpc_error_guard
    def ListProducts(self, request, context):
        items = self._svc.list_products()
        return platform_pb2.ProductListProto(
            items=[
                platform_pb2.ProductProto(
                    id=p.id,
                    name=p.name,
                    category=p.category,
                    status=p.status,
                    description=p.description or "",
                    owner_id=p.owner_id,
                )
                for p in items
            ]
        )

    @grpc_error_guard
    def ListTeams(self, request, context):
        items = self._svc.list_teams(product_id=request.product_id or None)
        return platform_pb2.TeamListProto(
            items=[
                platform_pb2.TeamProto(
                    id=t.id,
                    name=t.name,
                    role=t.role,
                    product_id=t.product_id or "",
                    member_ids=t.member_ids,
                )
                for t in items
            ]
        )


class UserServicer(platform_pb2_grpc.UserServiceServicer):
    def __init__(self, svc: UserService) -> None:
        self._svc = svc

    @staticmethod
    def _to_proto(u) -> platform_pb2.UserProto:
        return platform_pb2.UserProto(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role,
            team_id=u.team_id or "",
            expertise=u.expertise or "",
        )

    @grpc_error_guard
    def GetUser(self, request, context):
        return self._to_proto(self._svc.get_user(request.user_id))

    @grpc_error_guard
    def ListUsers(self, request, context):
        return platform_pb2.UserListProto(
            items=[self._to_proto(u) for u in self._svc.list_users()]
        )

    @grpc_error_guard
    def CheckPermission(self, request, context):
        return self._to_proto(self._svc.check_permission(request.user_id, request.action))


class NotificationServicer(platform_pb2_grpc.NotificationServiceServicer):
    def __init__(self, svc: NotificationService) -> None:
        self._svc = svc

    @staticmethod
    def _to_proto(n) -> platform_pb2.NotificationProto:
        return platform_pb2.NotificationProto(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            message=n.message,
            entity_type=n.entity_type,
            entity_id=n.entity_id,
            is_read=n.is_read,
            created_at=n.created_at,
        )

    @grpc_error_guard
    def ListNotifications(self, request, context):
        items = self._svc.list_notifications(request.user_id, request.unread_only)
        return platform_pb2.NotificationListProto(items=[self._to_proto(n) for n in items])

    @grpc_error_guard
    def CreateNotification(self, request, context):
        n = self._svc.create_notification(
            user_id=request.user_id,
            message=request.message,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            notif_type=request.notif_type or "IN_APP",
        )
        return self._to_proto(n)

    @grpc_error_guard
    def MarkRead(self, request, context):
        return self._to_proto(self._svc.mark_read(request.notification_id))


class IdeaPortalServicer(platform_pb2_grpc.IdeaPortalServiceServicer):
    def __init__(self, svc: IdeaPortalService) -> None:
        self._svc = svc

    @staticmethod
    def _to_proto(i) -> platform_pb2.IdeaProto:
        return platform_pb2.IdeaProto(
            id=i.id,
            product_id=i.product_id,
            title=i.title,
            description=i.description,
            expected_effect=i.expected_effect,
            category=i.category,
            author_name=i.author_name,
            status=i.status,
            hypothesis_id=i.hypothesis_id or "",
        )

    @grpc_error_guard
    def ListIdeas(self, request, context):
        return platform_pb2.IdeaListProto(
            items=[self._to_proto(i) for i in self._svc.list_ideas()]
        )

    @grpc_error_guard
    def SubmitIdea(self, request, context):
        i = self._svc.submit_idea(
            product_id=request.product_id,
            title=request.title,
            description=request.description,
            expected_effect=request.expected_effect,
            category=request.category,
            author_name=request.author_name,
            hypothesis_id=request.hypothesis_id,
        )
        return self._to_proto(i)


class FileStorageServicer(platform_pb2_grpc.FileStorageServiceServicer):
    def __init__(self, svc: FileStorageService) -> None:
        self._svc = svc

    @grpc_error_guard
    def ListAttachments(self, request, context):
        items = self._svc.list_attachments(request.entity_type, request.entity_id)
        return platform_pb2.AttachmentListProto(
            items=[
                platform_pb2.AttachmentProto(
                    id=a.id,
                    entity_type=a.entity_type,
                    entity_id=a.entity_id,
                    file_name=a.file_name,
                    file_url=a.file_url,
                    file_size=a.file_size,
                    uploaded_by=a.uploaded_by,
                )
                for a in items
            ]
        )


class AuditServicer(platform_pb2_grpc.AuditServiceServicer):
    def __init__(self, svc: AuditService) -> None:
        self._svc = svc

    @staticmethod
    def _to_proto(a) -> platform_pb2.ActivityLogProto:
        return platform_pb2.ActivityLogProto(
            id=a.id,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            user_id=a.user_id,
            action=a.action,
            old_value=a.old_value or "",
            new_value=a.new_value or "",
            timestamp=a.timestamp,
        )

    @grpc_error_guard
    def ListActivityLogs(self, request, context):
        items = self._svc.list_activity_logs(request.entity_type, request.entity_id)
        return platform_pb2.ActivityLogListProto(items=[self._to_proto(a) for a in items])

    @grpc_error_guard
    def RecordAction(self, request, context):
        a = self._svc.record_action(
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            user_id=request.user_id,
            action=request.action,
            old_value=request.old_value or None,
            new_value=request.new_value or None,
        )
        return self._to_proto(a)


class IntegrationServicer(platform_pb2_grpc.IntegrationServiceServicer):
    def __init__(self, svc: IntegrationService) -> None:
        self._svc = svc

    @grpc_error_guard
    def GetBacklogTask(self, request, context):
        return backlog_to_proto(self._svc.get_backlog_task(request.hypothesis_id))

    @grpc_error_guard
    def CreateExternalTask(self, request, context):
        return backlog_to_proto(
            self._svc.create_external_task(request.hypothesis_id, request.idempotency_key)
        )


class AuthServicer(platform_pb2_grpc.AuthServiceServicer):
    def __init__(self, svc: AuthService) -> None:
        self._svc = svc

    @staticmethod
    def _token_to_proto(res) -> platform_pb2.AuthTokenProto:
        return platform_pb2.AuthTokenProto(
            access_token=res.access_token,
            token_type=res.token_type,
            session_id=res.session_id,
            expires_in=res.expires_in,
            user=platform_pb2.AuthUserProto(
                id=res.user.id,
                name=res.user.name,
                email=res.user.email,
                role=res.user.role,
                created_at=res.user.created_at,
            ),
        )

    @grpc_error_guard
    def Register(self, request, context):
        return self._token_to_proto(
            self._svc.register(request.name, request.email, request.password, request.role)
        )

    @grpc_error_guard
    def Login(self, request, context):
        return self._token_to_proto(self._svc.login(request.email, request.password))

    @grpc_error_guard
    def VerifyTokenAndSession(self, request, context):
        u = self._svc.verify_token_and_session(request.token)
        return platform_pb2.AuthenticatedUserProto(
            user_id=u.user_id,
            name=u.name,
            email=u.email,
            role=u.role,
            session_id=u.session_id,
        )

    @grpc_error_guard
    def Logout(self, request, context):
        return platform_pb2.LogoutResponse(success=self._svc.logout(request.token))


def build_service_registry(
    redis_client=None, session_ttl_seconds: Optional[int] = None
) -> ServiceRegistry:
    h_conn = connect_sqlite(HypothesisServiceConfig().db_path, check_same_thread=False)
    h_repo = HypothesisRepository(h_conn)
    seed_hypothesis_db(h_conn)

    r_conn = connect_sqlite(ResearchServiceConfig().db_path, check_same_thread=False)
    r_repo = ResearchRepository(r_conn)
    seed_research_db(r_conn)

    rep_conn = connect_sqlite(ReportServiceConfig().db_path, check_same_thread=False)
    rep_repo = ReportRepository(rep_conn)
    seed_report_db(rep_conn)

    road_conn = connect_sqlite(RoadmapServiceConfig().db_path, check_same_thread=False)
    road_repo = RoadmapRepository(road_conn)
    seed_roadmap_db(road_conn)

    ana_conn = connect_sqlite(AnalyticsServiceConfig().db_path, check_same_thread=False)
    ana_repo = AnalyticsRepository(ana_conn)
    seed_analytics_db(ana_conn)

    prod_conn = connect_sqlite(ProductServiceConfig().db_path, check_same_thread=False)
    prod_repo = ProductRepository(prod_conn)
    seed_product_db(prod_conn)

    usr_conn = connect_sqlite(UserServiceConfig().db_path, check_same_thread=False)
    usr_repo = UserRepository(usr_conn)
    seed_user_db(usr_conn)

    not_conn = connect_sqlite(NotificationServiceConfig().db_path, check_same_thread=False)
    not_repo = NotificationRepository(not_conn)
    seed_notification_db(not_conn)

    idea_conn = connect_sqlite(IdeaPortalServiceConfig().db_path, check_same_thread=False)
    idea_repo = IdeaPortalRepository(idea_conn)
    seed_idea_db(idea_conn)

    fs_conn = connect_sqlite(FileStorageServiceConfig().db_path, check_same_thread=False)
    fs_repo = FileStorageRepository(fs_conn)
    seed_file_storage_db(fs_conn)

    aud_conn = connect_sqlite(AuditServiceConfig().db_path, check_same_thread=False)
    aud_repo = AuditRepository(aud_conn)
    seed_audit_db(aud_conn)

    intg_conn = connect_sqlite(IntegrationServiceConfig().db_path, check_same_thread=False)
    intg_repo = IntegrationRepository(intg_conn)
    seed_integration_db(intg_conn)

    auth_cfg = AuthServiceConfig(
        session_ttl_seconds=session_ttl_seconds
        if session_ttl_seconds is not None
        else AuthServiceConfig().session_ttl_seconds
    )
    auth_conn = connect_sqlite(get_db_path(auth_cfg.db_filename), check_same_thread=False)
    auth_repo = AuthRepository(auth_conn)
    seed_auth_db(auth_conn)
    r_client = redis_client if redis_client is not None else create_redis_client(auth_cfg.redis_url)
    session_store = RedisSessionStore(r_client)

    return ServiceRegistry(
        hypothesis=HypothesisService(h_repo),
        research=ResearchService(r_repo),
        report=ReportService(rep_repo),
        roadmap=RoadmapService(road_repo),
        analytics=AnalyticsService(ana_repo),
        product=ProductService(prod_repo),
        user=UserService(usr_repo),
        notification=NotificationService(not_repo),
        idea_portal=IdeaPortalService(idea_repo),
        file_storage=FileStorageService(fs_repo),
        audit=AuditService(aud_repo),
        integration=IntegrationService(intg_repo),
        auth=AuthService(auth_repo, session_store, config=auth_cfg),
        redis_client=r_client,
    )


def start_grpc_server(
    port: int = 0,
    redis_client=None,
    session_ttl_seconds: Optional[int] = None,
) -> tuple[grpc.Server, int, ServiceRegistry]:
    """Запускает реальный gRPC-сервер и регистрирует все 13 сервисов."""
    registry = build_service_registry(
        redis_client=redis_client, session_ttl_seconds=session_ttl_seconds
    )
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    platform_pb2_grpc.add_HypothesisServiceServicer_to_server(
        HypothesisServicer(registry.hypothesis), server
    )
    platform_pb2_grpc.add_ResearchServiceServicer_to_server(
        ResearchServicer(registry.research), server
    )
    platform_pb2_grpc.add_ReportServiceServicer_to_server(
        ReportServicer(registry.report), server
    )
    platform_pb2_grpc.add_RoadmapServiceServicer_to_server(
        RoadmapServicer(registry.roadmap), server
    )
    platform_pb2_grpc.add_AnalyticsServiceServicer_to_server(
        AnalyticsServicer(registry.analytics), server
    )
    platform_pb2_grpc.add_ProductServiceServicer_to_server(
        ProductServicer(registry.product), server
    )
    platform_pb2_grpc.add_UserServiceServicer_to_server(
        UserServicer(registry.user), server
    )
    platform_pb2_grpc.add_NotificationServiceServicer_to_server(
        NotificationServicer(registry.notification), server
    )
    platform_pb2_grpc.add_IdeaPortalServiceServicer_to_server(
        IdeaPortalServicer(registry.idea_portal), server
    )
    platform_pb2_grpc.add_FileStorageServiceServicer_to_server(
        FileStorageServicer(registry.file_storage), server
    )
    platform_pb2_grpc.add_AuditServiceServicer_to_server(
        AuditServicer(registry.audit), server
    )
    platform_pb2_grpc.add_IntegrationServiceServicer_to_server(
        IntegrationServicer(registry.integration), server
    )
    platform_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthServicer(registry.auth), server
    )
    bound_port = server.add_insecure_port(f"127.0.0.1:{port}")
    server.start()
    return server, bound_port, registry
