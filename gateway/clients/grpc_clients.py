"""Реальные gRPC-клиенты внутренних микросервисов и сборка подключения к gRPC и Kafka."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import wraps
from typing import Optional

import grpc

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
from grpc_layer.server import ServiceRegistry, start_grpc_server
from kafka_layer.consumer import KafkaEventConsumer, register_platform_consumers
from kafka_layer.producer import KafkaEventProducer
from protos import platform_pb2, platform_pb2_grpc
from services.analytics_service.models import DashboardMetricModel
from services.audit_service.models import ActivityLogModel
from services.auth_service.models import AuthenticatedUserModel, AuthTokenModel, AuthUserModel
from services.auth_service.service import AuthService
from services.file_storage_service.models import AttachmentModel
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
from shared.cache import RedisCache
from shared.resilience import RetryPolicy, execute_with_retry


class _TimeoutInterceptor(grpc.UnaryUnaryClientInterceptor):
    def __init__(self, timeout_seconds: float) -> None:
        self._timeout = timeout_seconds

    def intercept_unary_unary(self, continuation, client_call_details, request):
        if client_call_details.timeout is None:
            client_call_details = client_call_details._replace(timeout=self._timeout)
        return continuation(client_call_details, request)


def _rpc_guard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        policy = getattr(args[0], "_policy", RetryPolicy()) if args else RetryPolicy()
        return execute_with_retry(
            fn.__qualname__, policy, lambda _t: fn(*args, **kwargs)
        )

    return wrapper


def _proto_to_hyp(p: platform_pb2.HypothesisProto) -> HypothesisModel:
    return HypothesisModel(
        id=p.id,
        title=p.title,
        description=p.description,
        status=p.status,
        priority=p.priority,
        rice_score=p.rice_score if p.has_rice_score else None,
        product_id=p.product_id,
        owner_id=p.owner_id,
        created_at=p.created_at,
    )


def _proto_to_res(p: platform_pb2.ResearchProto) -> ResearchModel:
    return ResearchModel(
        id=p.id,
        title=p.title,
        status=p.status,
        type=p.type,
        method=p.method,
        target_audience=p.target_audience,
        sample_size=p.sample_size,
        start_date=p.start_date or None,
        end_date=p.end_date or None,
        hypothesis_id=p.hypothesis_id,
        assignee_id=p.assignee_id,
    )


def _proto_to_rice(p: platform_pb2.RICEScoreProto) -> Optional[RICEScoreModel]:
    if not p.found:
        return None
    return RICEScoreModel(
        id=p.id,
        hypothesis_id=p.hypothesis_id,
        reach=p.reach,
        impact=p.impact,
        confidence=p.confidence,
        effort=p.effort,
        calculated_score=p.calculated_score,
    )


def _proto_to_backlog(p: platform_pb2.BacklogTaskProto) -> Optional[BacklogTaskModel]:
    if not p.found:
        return None
    return BacklogTaskModel(
        id=p.id,
        hypothesis_id=p.hypothesis_id,
        idempotency_key=p.idempotency_key,
        external_system=p.external_system,
        external_key=p.external_key,
        external_url=p.external_url,
        status=p.status,
        synced_at=p.synced_at,
    )


class GrpcHypothesisClient(HypothesisClient):
    def __init__(
        self,
        channel: grpc.Channel,
        cache: Optional[RedisCache] = None,
        policy: Optional[RetryPolicy] = None,
    ) -> None:
        self._stub = platform_pb2_grpc.HypothesisServiceStub(channel)
        self._cache = cache
        self._policy = policy or RetryPolicy()

    @_rpc_guard
    def get_hypothesis(self, hypothesis_id: str) -> HypothesisModel:
        return _proto_to_hyp(
            self._stub.GetHypothesis(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        )

    @_rpc_guard
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
        resp = self._stub.ListHypotheses(
            platform_pb2.ListHypothesesRequest(
                product_id=product_id or "",
                status=status or "",
                priority=priority or "",
                owner_id=owner_id or "",
                has_min_rice_score=min_rice_score is not None,
                min_rice_score=float(min_rice_score) if min_rice_score is not None else 0.0,
                search=search or "",
                sort_by=sort_by,
                sort_dir=sort_dir,
            )
        )
        return [_proto_to_hyp(i) for i in resp.items]

    @_rpc_guard
    def get_summary(self, product_id: Optional[str] = None) -> HypothesesSummaryModel:
        cache_key = f"cache:summary:{product_id or 'all'}"
        if self._cache is not None:
            cached = self._cache.get_json(cache_key)
            if cached is not None:
                return HypothesesSummaryModel(
                    total_count=cached["total_count"],
                    by_status=[StatusCountModel(**x) for x in cached["by_status"]],
                    by_priority=[PriorityCountModel(**x) for x in cached["by_priority"]],
                    avg_rice_score=cached["avg_rice_score"],
                    max_rice_score=cached["max_rice_score"],
                    confirmed_rate=cached["confirmed_rate"],
                    in_backlog_count=cached["in_backlog_count"],
                )
        s = self._stub.GetSummary(platform_pb2.GetSummaryRequest(product_id=product_id or ""))
        result = HypothesesSummaryModel(
            total_count=s.total_count,
            by_status=[StatusCountModel(status=x.status, count=x.count) for x in s.by_status],
            by_priority=[PriorityCountModel(priority=x.priority, count=x.count) for x in s.by_priority],
            avg_rice_score=s.avg_rice_score if s.has_avg_rice_score else None,
            max_rice_score=s.max_rice_score if s.has_max_rice_score else None,
            confirmed_rate=s.confirmed_rate,
            in_backlog_count=s.in_backlog_count,
        )
        if self._cache is not None:
            self._cache.set_json(cache_key, asdict(result))
        return result

    @_rpc_guard
    def get_template(self, hypothesis_id: str) -> Optional[HypothesisTemplateModel]:
        t = self._stub.GetTemplate(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        if not t.found:
            return None
        return HypothesisTemplateModel(
            id=t.id,
            hypothesis_id=t.hypothesis_id,
            if_action=t.if_action,
            then_result=t.then_result,
            because_assumption=t.because_assumption,
        )

    @_rpc_guard
    def get_rice_score(self, hypothesis_id: str) -> Optional[RICEScoreModel]:
        return _proto_to_rice(
            self._stub.GetRiceScore(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        )

    @_rpc_guard
    def list_comments(self, entity_type: str, entity_id: str) -> list[CommentModel]:
        resp = self._stub.ListComments(
            platform_pb2.ListCommentsRequest(entity_type=entity_type, entity_id=entity_id)
        )
        return [
            CommentModel(
                id=c.id,
                entity_type=c.entity_type,
                entity_id=c.entity_id,
                author_id=c.author_id,
                text=c.text,
                created_at=c.created_at,
            )
            for c in resp.items
        ]

    @_rpc_guard
    def find_duplicate_hypotheses(
        self, title: str, description: str, product_id: str
    ) -> list[DuplicateCandidateModel]:
        resp = self._stub.FindDuplicateHypotheses(
            platform_pb2.FindDuplicatesRequest(
                title=title, description=description, product_id=product_id
            )
        )
        return [
            DuplicateCandidateModel(
                hypothesis_id=c.hypothesis_id,
                title=c.title,
                similarity=c.similarity,
                status=c.status,
            )
            for c in resp.items
        ]

    @_rpc_guard
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
        return _proto_to_hyp(
            self._stub.CreateHypothesis(
                platform_pb2.CreateHypothesisRequest(
                    title=title,
                    description=description,
                    product_id=product_id,
                    owner_id=owner_id,
                    priority=priority,
                    if_action=if_action,
                    then_result=then_result,
                    because_assumption=because_assumption,
                )
            )
        )

    @_rpc_guard
    def calculate_rice(
        self, hypothesis_id: str, reach: int, impact: float, confidence: float, effort: int
    ) -> RICEScoreModel:
        res = _proto_to_rice(
            self._stub.CalculateRICE(
                platform_pb2.CalculateRICERequest(
                    hypothesis_id=hypothesis_id,
                    reach=reach,
                    impact=impact,
                    confidence=confidence,
                    effort=effort,
                )
            )
        )
        assert res is not None
        return res

    @_rpc_guard
    def apply_research_result(self, hypothesis_id: str, target_status: str) -> HypothesisModel:
        return _proto_to_hyp(
            self._stub.ApplyResearchResult(
                platform_pb2.ApplyResearchResultRequest(
                    hypothesis_id=hypothesis_id, target_status=target_status
                )
            )
        )

    @_rpc_guard
    def begin_export(self, hypothesis_id: str) -> HypothesisModel:
        return _proto_to_hyp(
            self._stub.BeginExport(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        )

    @_rpc_guard
    def complete_export(self, hypothesis_id: str) -> HypothesisModel:
        return _proto_to_hyp(
            self._stub.CompleteExport(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        )

    @_rpc_guard
    def rollback_export(self, hypothesis_id: str) -> HypothesisModel:
        return _proto_to_hyp(
            self._stub.RollbackExport(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        )

    @_rpc_guard
    def add_comment(
        self, entity_type: str, entity_id: str, author_id: str, text: str
    ) -> CommentModel:
        c = self._stub.AddComment(
            platform_pb2.AddCommentRequest(
                entity_type=entity_type, entity_id=entity_id, author_id=author_id, text=text
            )
        )
        return CommentModel(
            id=c.id,
            entity_type=c.entity_type,
            entity_id=c.entity_id,
            author_id=c.author_id,
            text=c.text,
            created_at=c.created_at,
        )


class GrpcResearchClient(ResearchClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.ResearchServiceStub(channel)

    @_rpc_guard
    def get_research(self, research_id: str) -> ResearchModel:
        return _proto_to_res(
            self._stub.GetResearch(platform_pb2.GetResearchRequest(research_id=research_id))
        )

    @_rpc_guard
    def list_researches(
        self,
        hypothesis_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee_id: Optional[str] = None,
        sort_by: str = "start_date",
        sort_dir: str = "DESC",
    ) -> list[ResearchModel]:
        resp = self._stub.ListResearches(
            platform_pb2.ListResearchesRequest(
                hypothesis_id=hypothesis_id or "",
                status=status or "",
                assignee_id=assignee_id or "",
                sort_by=sort_by,
                sort_dir=sort_dir,
            )
        )
        return [_proto_to_res(r) for r in resp.items]

    @_rpc_guard
    def get_design(self, research_id: str) -> Optional[ResearchDesignModel]:
        d = self._stub.GetDesign(platform_pb2.GetResearchRequest(research_id=research_id))
        if not d.found:
            return None
        return ResearchDesignModel(
            id=d.id,
            research_id=d.research_id,
            goal=d.goal,
            questions=d.questions,
            success_criteria=d.success_criteria,
            user_stories=d.user_stories or None,
        )

    @_rpc_guard
    def list_insights(self, research_id: str) -> list[InsightModel]:
        resp = self._stub.ListInsights(platform_pb2.GetResearchRequest(research_id=research_id))
        return [
            InsightModel(
                id=i.id,
                research_id=i.research_id,
                text=i.text,
                created_by=i.created_by,
                created_at=i.created_at,
            )
            for i in resp.items
        ]

    @_rpc_guard
    def list_notes(self, research_id: str) -> list[ResearchNoteModel]:
        resp = self._stub.ListNotes(platform_pb2.GetResearchRequest(research_id=research_id))
        return [
            ResearchNoteModel(
                id=n.id,
                research_id=n.research_id,
                text=n.text,
                author_id=n.author_id,
                created_at=n.created_at,
            )
            for n in resp.items
        ]

    @_rpc_guard
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
        return _proto_to_res(
            self._stub.CreateResearch(
                platform_pb2.CreateResearchRequest(
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
                    user_stories=user_stories or "",
                )
            )
        )

    @_rpc_guard
    def add_note(self, research_id: str, author_id: str, text: str) -> ResearchNoteModel:
        n = self._stub.AddNote(
            platform_pb2.AddResearchTextRequest(research_id=research_id, user_id=author_id, text=text)
        )
        return ResearchNoteModel(
            id=n.id,
            research_id=n.research_id,
            text=n.text,
            author_id=n.author_id,
            created_at=n.created_at,
        )

    @_rpc_guard
    def add_insight(self, research_id: str, created_by: str, text: str) -> InsightModel:
        i = self._stub.AddInsight(
            platform_pb2.AddResearchTextRequest(research_id=research_id, user_id=created_by, text=text)
        )
        return InsightModel(
            id=i.id,
            research_id=i.research_id,
            text=i.text,
            created_by=i.created_by,
            created_at=i.created_at,
        )

    @_rpc_guard
    def complete_research(self, research_id: str) -> ResearchModel:
        return _proto_to_res(
            self._stub.CompleteResearch(platform_pb2.GetResearchRequest(research_id=research_id))
        )

    @_rpc_guard
    def mark_completed(self, research_id: str) -> ResearchModel:
        return _proto_to_res(
            self._stub.MarkCompleted(platform_pb2.GetResearchRequest(research_id=research_id))
        )


class GrpcReportClient(ReportClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.ReportServiceStub(channel)

    @_rpc_guard
    def get_report_by_research(self, research_id: str) -> Optional[ReportModel]:
        r = self._stub.GetReportByResearch(platform_pb2.GetResearchRequest(research_id=research_id))
        if not r.found:
            return None
        return ReportModel(
            id=r.id,
            research_id=r.research_id,
            conclusion=r.conclusion,
            recommendations=r.recommendations,
            file_url=r.file_url or None,
            created_at=r.created_at,
        )

    @_rpc_guard
    def publish_report(
        self,
        research_id: str,
        conclusion: str,
        recommendations: str,
        file_url: Optional[str] = None,
    ) -> ReportModel:
        r = self._stub.PublishReport(
            platform_pb2.PublishReportRequest(
                research_id=research_id,
                conclusion=conclusion,
                recommendations=recommendations,
                file_url=file_url or "",
            )
        )
        return ReportModel(
            id=r.id,
            research_id=r.research_id,
            conclusion=r.conclusion,
            recommendations=r.recommendations,
            file_url=r.file_url or None,
            created_at=r.created_at,
        )


class GrpcRoadmapClient(RoadmapClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.RoadmapServiceStub(channel)

    @_rpc_guard
    def list_roadmap(self, sort_dir: str = "ASC") -> list[RoadmapItemModel]:
        resp = self._stub.ListRoadmap(platform_pb2.ListRoadmapRequest(sort_dir=sort_dir))
        return [
            RoadmapItemModel(
                id=i.id,
                hypothesis_id=i.hypothesis_id,
                hypothesis_title=i.hypothesis_title,
                start_date=i.start_date,
                end_date=i.end_date,
                duration=i.duration,
                dependencies=list(i.dependencies),
                assignee_id=i.assignee_id,
            )
            for i in resp.items
        ]

    @_rpc_guard
    def schedule_item(
        self,
        hypothesis_id: str,
        hypothesis_title: str,
        start_date: str,
        end_date: str,
        dependencies: list[str],
        assignee_id: str,
    ) -> RoadmapItemModel:
        i = self._stub.ScheduleItem(
            platform_pb2.ScheduleRoadmapRequest(
                hypothesis_id=hypothesis_id,
                hypothesis_title=hypothesis_title,
                start_date=start_date,
                end_date=end_date,
                dependencies=dependencies,
                assignee_id=assignee_id,
            )
        )
        return RoadmapItemModel(
            id=i.id,
            hypothesis_id=i.hypothesis_id,
            hypothesis_title=i.hypothesis_title,
            start_date=i.start_date,
            end_date=i.end_date,
            duration=i.duration,
            dependencies=list(i.dependencies),
            assignee_id=i.assignee_id,
        )


class GrpcAnalyticsClient(AnalyticsClient):
    def __init__(
        self,
        channel: grpc.Channel,
        cache: Optional[RedisCache] = None,
        policy: Optional[RetryPolicy] = None,
    ) -> None:
        self._stub = platform_pb2_grpc.AnalyticsServiceStub(channel)
        self._cache = cache
        self._policy = policy or RetryPolicy()

    @_rpc_guard
    def get_dashboard_metrics(
        self, product_id: Optional[str] = None, period: Optional[str] = None
    ) -> list[DashboardMetricModel]:
        cache_key = f"cache:metrics:{product_id or 'all'}:{period or 'all'}"
        if self._cache is not None:
            cached = self._cache.get_json(cache_key)
            if cached is not None:
                return [DashboardMetricModel(**m) for m in cached]
        resp = self._stub.GetDashboardMetrics(
            platform_pb2.GetDashboardMetricsRequest(
                product_id=product_id or "", period=period or ""
            )
        )
        items = [
            DashboardMetricModel(
                id=m.id,
                metric_type=m.metric_type,
                product_id=m.product_id,
                period=m.period,
                value=m.value,
            )
            for m in resp.items
        ]
        if self._cache is not None:
            self._cache.set_json(cache_key, [asdict(m) for m in items])
        return items


class GrpcProductClient(ProductClient):
    def __init__(
        self,
        channel: grpc.Channel,
        cache: Optional[RedisCache] = None,
        policy: Optional[RetryPolicy] = None,
    ) -> None:
        self._stub = platform_pb2_grpc.ProductServiceStub(channel)
        self._cache = cache
        self._policy = policy or RetryPolicy()

    @_rpc_guard
    def get_product(self, product_id: str) -> ProductModel:
        cache_key = f"cache:product:{product_id}"
        if self._cache is not None:
            cached = self._cache.get_json(cache_key)
            if cached is not None:
                return ProductModel(**cached)
        p = self._stub.GetProduct(platform_pb2.GetProductRequest(product_id=product_id))
        model = ProductModel(
            id=p.id,
            name=p.name,
            category=p.category,
            status=p.status,
            description=p.description or None,
            owner_id=p.owner_id,
        )
        if self._cache is not None:
            self._cache.set_json(cache_key, asdict(model))
        return model

    @_rpc_guard
    def list_products(self) -> list[ProductModel]:
        cache_key = "cache:products:all"
        if self._cache is not None:
            cached = self._cache.get_json(cache_key)
            if cached is not None:
                return [ProductModel(**p) for p in cached]
        resp = self._stub.ListProducts(platform_pb2.Empty())
        items = [
            ProductModel(
                id=p.id,
                name=p.name,
                category=p.category,
                status=p.status,
                description=p.description or None,
                owner_id=p.owner_id,
            )
            for p in resp.items
        ]
        if self._cache is not None:
            self._cache.set_json(cache_key, [asdict(p) for p in items])
        return items

    @_rpc_guard
    def list_teams(self, product_id: Optional[str] = None) -> list[TeamModel]:
        resp = self._stub.ListTeams(platform_pb2.GetProductRequest(product_id=product_id or ""))
        return [
            TeamModel(
                id=t.id,
                name=t.name,
                role=t.role,
                product_id=t.product_id or None,
                member_ids=list(t.member_ids),
            )
            for t in resp.items
        ]


class GrpcUserClient(UserClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.UserServiceStub(channel)

    @staticmethod
    def _from_proto(u: platform_pb2.UserProto) -> UserModel:
        return UserModel(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role,
            team_id=u.team_id or None,
            expertise=u.expertise or None,
        )

    @_rpc_guard
    def get_user(self, user_id: str) -> UserModel:
        return self._from_proto(self._stub.GetUser(platform_pb2.GetUserRequest(user_id=user_id)))

    @_rpc_guard
    def list_users(self) -> list[UserModel]:
        resp = self._stub.ListUsers(platform_pb2.Empty())
        return [self._from_proto(u) for u in resp.items]

    @_rpc_guard
    def check_permission(self, user_id: str, action: str) -> UserModel:
        return self._from_proto(
            self._stub.CheckPermission(
                platform_pb2.CheckPermissionRequest(user_id=user_id, action=action)
            )
        )


class GrpcNotificationClient(NotificationClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.NotificationServiceStub(channel)

    @staticmethod
    def _from_proto(n: platform_pb2.NotificationProto) -> NotificationModel:
        return NotificationModel(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            message=n.message,
            entity_type=n.entity_type,
            entity_id=n.entity_id,
            is_read=n.is_read,
            created_at=n.created_at,
        )

    @_rpc_guard
    def list_notifications(self, user_id: str, unread_only: bool = False) -> list[NotificationModel]:
        resp = self._stub.ListNotifications(
            platform_pb2.ListNotificationsRequest(user_id=user_id, unread_only=unread_only)
        )
        return [self._from_proto(n) for n in resp.items]

    @_rpc_guard
    def create_notification(
        self,
        user_id: str,
        message: str,
        entity_type: str,
        entity_id: str,
        notif_type: str = "IN_APP",
    ) -> NotificationModel:
        return self._from_proto(
            self._stub.CreateNotification(
                platform_pb2.CreateNotificationRequest(
                    user_id=user_id,
                    message=message,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    notif_type=notif_type,
                )
            )
        )

    @_rpc_guard
    def mark_read(self, notification_id: str) -> NotificationModel:
        return self._from_proto(
            self._stub.MarkRead(platform_pb2.MarkReadRequest(notification_id=notification_id))
        )


class GrpcIdeaPortalClient(IdeaPortalClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.IdeaPortalServiceStub(channel)

    @staticmethod
    def _from_proto(i: platform_pb2.IdeaProto) -> IdeaModel:
        return IdeaModel(
            id=i.id,
            product_id=i.product_id,
            title=i.title,
            description=i.description,
            expected_effect=i.expected_effect,
            category=i.category,
            author_name=i.author_name,
            status=i.status,
            hypothesis_id=i.hypothesis_id or None,
        )

    @_rpc_guard
    def list_ideas(self) -> list[IdeaModel]:
        return [self._from_proto(i) for i in self._stub.ListIdeas(platform_pb2.Empty()).items]

    @_rpc_guard
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
        return self._from_proto(
            self._stub.SubmitIdea(
                platform_pb2.SubmitIdeaRequest(
                    product_id=product_id,
                    title=title,
                    description=description,
                    expected_effect=expected_effect,
                    category=category,
                    author_name=author_name,
                    hypothesis_id=hypothesis_id,
                )
            )
        )


class GrpcFileStorageClient(FileStorageClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.FileStorageServiceStub(channel)

    @_rpc_guard
    def list_attachments(self, entity_type: str, entity_id: str) -> list[AttachmentModel]:
        resp = self._stub.ListAttachments(
            platform_pb2.ListCommentsRequest(entity_type=entity_type, entity_id=entity_id)
        )
        return [
            AttachmentModel(
                id=a.id,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                file_name=a.file_name,
                file_url=a.file_url,
                file_size=a.file_size,
                uploaded_by=a.uploaded_by,
            )
            for a in resp.items
        ]


class GrpcAuditClient(AuditClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.AuditServiceStub(channel)

    @staticmethod
    def _from_proto(a: platform_pb2.ActivityLogProto) -> ActivityLogModel:
        return ActivityLogModel(
            id=a.id,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            user_id=a.user_id,
            action=a.action,
            old_value=a.old_value or None,
            new_value=a.new_value or None,
            timestamp=a.timestamp,
        )

    @_rpc_guard
    def list_activity_logs(self, entity_type: str, entity_id: str) -> list[ActivityLogModel]:
        resp = self._stub.ListActivityLogs(
            platform_pb2.ListCommentsRequest(entity_type=entity_type, entity_id=entity_id)
        )
        return [self._from_proto(a) for a in resp.items]

    @_rpc_guard
    def record_action(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        action: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
    ) -> ActivityLogModel:
        return self._from_proto(
            self._stub.RecordAction(
                platform_pb2.RecordActionRequest(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id,
                    action=action,
                    old_value=old_value or "",
                    new_value=new_value or "",
                )
            )
        )


class GrpcIntegrationClient(IntegrationClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.IntegrationServiceStub(channel)

    @_rpc_guard
    def get_backlog_task(self, hypothesis_id: str) -> Optional[BacklogTaskModel]:
        return _proto_to_backlog(
            self._stub.GetBacklogTask(platform_pb2.GetHypothesisRequest(hypothesis_id=hypothesis_id))
        )

    @_rpc_guard
    def create_external_task(self, hypothesis_id: str, idempotency_key: str) -> BacklogTaskModel:
        res = _proto_to_backlog(
            self._stub.CreateExternalTask(
                platform_pb2.CreateExternalTaskRequest(
                    hypothesis_id=hypothesis_id, idempotency_key=idempotency_key
                )
            )
        )
        assert res is not None
        return res


class GrpcAuthClient(AuthClient):
    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = platform_pb2_grpc.AuthServiceStub(channel)

    @staticmethod
    def _token_from_proto(t: platform_pb2.AuthTokenProto) -> AuthTokenModel:
        return AuthTokenModel(
            access_token=t.access_token,
            token_type=t.token_type,
            session_id=t.session_id,
            expires_in=t.expires_in,
            user=AuthUserModel(
                id=t.user.id,
                name=t.user.name,
                email=t.user.email,
                password_hash="",
                role=t.user.role,
                created_at=t.user.created_at,
            ),
        )

    @_rpc_guard
    def register(
        self, name: str, email: str, password: str, role: str = "PM"
    ) -> AuthTokenModel:
        return self._token_from_proto(
            self._stub.Register(
                platform_pb2.RegisterRequest(
                    name=name, email=email, password=password, role=role
                )
            )
        )

    @_rpc_guard
    def login(self, email: str, password: str) -> AuthTokenModel:
        return self._token_from_proto(
            self._stub.Login(platform_pb2.LoginRequest(email=email, password=password))
        )

    @_rpc_guard
    def verify_token_and_session(self, token: str) -> AuthenticatedUserModel:
        u = self._stub.VerifyTokenAndSession(platform_pb2.TokenRequest(token=token))
        return AuthenticatedUserModel(
            user_id=u.user_id,
            name=u.name,
            email=u.email,
            role=u.role,
            session_id=u.session_id,
        )

    @_rpc_guard
    def logout(self, token: str) -> bool:
        return bool(self._stub.Logout(platform_pb2.TokenRequest(token=token)).success)


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
    kafka_producer: KafkaEventProducer
    kafka_consumer: KafkaEventConsumer
    grpc_server: grpc.Server
    grpc_channel: grpc.Channel
    registry: ServiceRegistry
    cache: RedisCache
    retry_policy: RetryPolicy

    def shutdown(self) -> None:
        self.kafka_producer.close()
        self.grpc_channel.close()
        self.grpc_server.stop(grace=0)


def build_grpc_clients(
    redis_client=None,
    session_ttl_seconds: Optional[int] = None,
    port: int = 0,
    retry_policy: Optional[RetryPolicy] = None,
) -> ServiceClients:
    """Запускает gRPC-сервер, подключает Kafka, Redis-кеш, timeout/retry и возвращает gRPC-клиенты."""
    policy = retry_policy or RetryPolicy()
    server, bound_port, registry = start_grpc_server(
        port=port, redis_client=redis_client, session_ttl_seconds=session_ttl_seconds
    )
    cache = RedisCache(registry.redis_client, default_ttl_seconds=300)
    producer = KafkaEventProducer()
    consumer = register_platform_consumers(registry, producer.broker, cache=cache)
    raw_channel = grpc.insecure_channel(f"127.0.0.1:{bound_port}")
    channel = grpc.intercept_channel(raw_channel, _TimeoutInterceptor(policy.timeout_seconds))

    return ServiceClients(
        hypothesis=GrpcHypothesisClient(channel, cache=cache, policy=policy),
        research=GrpcResearchClient(channel),
        report=GrpcReportClient(channel),
        roadmap=GrpcRoadmapClient(channel),
        analytics=GrpcAnalyticsClient(channel, cache=cache, policy=policy),
        product=GrpcProductClient(channel, cache=cache, policy=policy),
        user=GrpcUserClient(channel),
        notification=GrpcNotificationClient(channel),
        idea_portal=GrpcIdeaPortalClient(channel),
        file_storage=GrpcFileStorageClient(channel),
        audit=GrpcAuditClient(channel),
        integration=GrpcIntegrationClient(channel),
        auth=GrpcAuthClient(channel),
        auth_service=registry.auth,
        kafka_producer=producer,
        kafka_consumer=consumer,
        grpc_server=server,
        grpc_channel=raw_channel,
        registry=registry,
        cache=cache,
        retry_policy=policy,
    )
