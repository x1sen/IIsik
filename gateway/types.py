"""GraphQL-типы, перечисления и входные структуры на основе ЛР2."""

from __future__ import annotations

from enum import Enum
from typing import Optional

import strawberry
from strawberry.types import Info


@strawberry.enum
class HypothesisStatus(Enum):
    DRAFT = "DRAFT"
    VALIDATION = "VALIDATION"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    EXPORT_PENDING = "EXPORT_PENDING"
    IN_BACKLOG = "IN_BACKLOG"


@strawberry.enum
class Priority(Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


@strawberry.enum
class ResearchStatus(Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    REPORT_READY = "REPORT_READY"
    COMPLETED = "COMPLETED"


@strawberry.enum
class UserRole(Enum):
    PM = "PM"
    CX_EXPERT = "CX_EXPERT"
    AGILE_CENTER = "AGILE_CENTER"
    ADMIN = "ADMIN"


@strawberry.enum
class CommentEntityType(Enum):
    HYPOTHESIS = "HYPOTHESIS"
    RESEARCH = "RESEARCH"
    REPORT = "REPORT"


@strawberry.enum
class SortDirection(Enum):
    ASC = "ASC"
    DESC = "DESC"


@strawberry.enum
class HypothesisSortField(Enum):
    CREATED_AT = "created_at"
    RICE_SCORE = "rice_score"
    PRIORITY = "priority"
    TITLE = "title"


@strawberry.enum
class ResearchSortField(Enum):
    START_DATE = "start_date"
    STATUS = "status"
    TITLE = "title"
    SAMPLE_SIZE = "sample_size"


@strawberry.input
class FindDuplicatesInput:
    title: str
    description: str = ""
    product_id: str


@strawberry.input
class HypothesisFilterInput:
    product_id: Optional[strawberry.ID] = None
    status: Optional[HypothesisStatus] = None
    priority: Optional[Priority] = None
    owner_id: Optional[strawberry.ID] = None
    min_rice_score: Optional[float] = None
    search: Optional[str] = None


@strawberry.input
class HypothesisSortInput:
    field: HypothesisSortField = HypothesisSortField.CREATED_AT
    direction: SortDirection = SortDirection.DESC


@strawberry.input
class ResearchFilterInput:
    hypothesis_id: Optional[strawberry.ID] = None
    status: Optional[ResearchStatus] = None
    assignee_id: Optional[strawberry.ID] = None


@strawberry.input
class ResearchSortInput:
    field: ResearchSortField = ResearchSortField.START_DATE
    direction: SortDirection = SortDirection.DESC


@strawberry.input
class CreateHypothesisInput:
    title: str
    description: str
    product_id: strawberry.ID
    owner_id: strawberry.ID
    priority: Priority
    if_action: str
    then_result: str
    because_assumption: str


@strawberry.input
class CalculateRICEInput:
    hypothesis_id: strawberry.ID
    reach: int
    impact: float
    confidence: float
    effort: int
    user_id: strawberry.ID = strawberry.ID("user-001")


@strawberry.input
class ApplyResearchResultInput:
    hypothesis_id: strawberry.ID
    research_id: strawberry.ID
    status: HypothesisStatus
    user_id: strawberry.ID = strawberry.ID("user-002")


@strawberry.input
class ExportToBacklogInput:
    hypothesis_id: strawberry.ID
    user_id: strawberry.ID = strawberry.ID("user-001")


@strawberry.input
class CreateResearchInput:
    hypothesis_id: strawberry.ID
    title: str
    type: str
    method: str
    target_audience: str
    sample_size: int
    assignee_id: strawberry.ID
    goal: str
    questions: str
    success_criteria: str
    user_stories: Optional[str] = None


@strawberry.input
class AddResearchNoteInput:
    research_id: strawberry.ID
    text: str
    author_id: strawberry.ID = strawberry.ID("user-002")


@strawberry.input
class AddInsightInput:
    research_id: strawberry.ID
    text: str
    created_by: strawberry.ID = strawberry.ID("user-002")


@strawberry.input
class CreateReportInput:
    research_id: strawberry.ID
    conclusion: str
    recommendations: str
    file_url: Optional[str] = None
    author_id: strawberry.ID = strawberry.ID("user-002")


@strawberry.input
class CreateRoadmapItemInput:
    hypothesis_id: strawberry.ID
    start_date: str
    end_date: str
    dependencies: list[strawberry.ID] = strawberry.field(default_factory=list)
    assignee_id: strawberry.ID = strawberry.ID("user-001")


@strawberry.input
class SubmitIdeaInput:
    product_id: strawberry.ID
    title: str
    description: str
    expected_effect: str
    category: str
    author_name: str
    priority: Priority = Priority.P2
    owner_id: Optional[strawberry.ID] = None
    if_action: Optional[str] = None
    then_result: Optional[str] = None
    because_assumption: Optional[str] = None


@strawberry.input
class AddCommentInput:
    entity_type: CommentEntityType
    entity_id: strawberry.ID
    text: str
    author_id: strawberry.ID = strawberry.ID("user-001")


@strawberry.type
class UserType:
    id: strawberry.ID
    name: str
    email: str
    role: UserRole
    team_id: Optional[strawberry.ID]
    expertise: Optional[str]


@strawberry.type
class TeamType:
    id: strawberry.ID
    name: str
    role: str
    product_id: Optional[strawberry.ID]
    member_ids: list[strawberry.ID]


@strawberry.type
class ProductType:
    id: strawberry.ID
    name: str
    category: str
    status: str
    description: Optional[str]
    owner_id: strawberry.Private[str]

    @strawberry.field
    def owner(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.owner_id)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )

    @strawberry.field
    def teams(self, info: Info) -> list[TeamType]:
        items = info.context["clients"].product.list_teams(product_id=str(self.id))
        return [
            TeamType(
                id=strawberry.ID(t.id),
                name=t.name,
                role=t.role,
                product_id=strawberry.ID(t.product_id) if t.product_id else None,
                member_ids=[strawberry.ID(m) for m in t.member_ids],
            )
            for t in items
        ]


@strawberry.type
class HypothesisTemplateType:
    id: strawberry.ID
    if_action: str
    then_result: str
    because_assumption: str


@strawberry.type
class RICEScoreType:
    id: strawberry.ID
    reach: int
    impact: float
    confidence: float
    effort: int
    calculated_score: float


@strawberry.type
class CommentType:
    id: strawberry.ID
    entity_type: CommentEntityType
    entity_id: strawberry.ID
    text: str
    created_at: str
    author_id: strawberry.Private[str]

    @strawberry.field
    def author(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.author_id)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )


@strawberry.type
class BacklogTaskType:
    id: strawberry.ID
    hypothesis_id: strawberry.ID
    external_system: str
    external_key: str
    external_url: str
    status: str
    synced_at: str


@strawberry.type
class DuplicateCandidateType:
    hypothesis_id: strawberry.ID
    title: str
    similarity: float
    status: HypothesisStatus


@strawberry.type
class AttachmentType:
    id: strawberry.ID
    file_name: str
    file_url: str
    file_size: int


@strawberry.type
class HypothesisType:
    id: strawberry.ID
    title: str
    description: str
    status: HypothesisStatus
    priority: Priority
    created_at: str
    product_id: strawberry.Private[str]
    owner_id: strawberry.Private[str]

    @strawberry.field
    def product(self, info: Info) -> ProductType:
        p = info.context["clients"].product.get_product(self.product_id)
        return ProductType(
            id=strawberry.ID(p.id),
            name=p.name,
            category=p.category,
            status=p.status,
            description=p.description,
            owner_id=p.owner_id,
        )

    @strawberry.field
    def owner(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.owner_id)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )

    @strawberry.field
    def template(self, info: Info) -> Optional[HypothesisTemplateType]:
        t = info.context["clients"].hypothesis.get_template(str(self.id))
        if not t:
            return None
        return HypothesisTemplateType(
            id=strawberry.ID(t.id),
            if_action=t.if_action,
            then_result=t.then_result,
            because_assumption=t.because_assumption,
        )

    @strawberry.field
    def rice_score(self, info: Info) -> Optional[RICEScoreType]:
        r = info.context["clients"].hypothesis.get_rice_score(str(self.id))
        if not r:
            return None
        return RICEScoreType(
            id=strawberry.ID(r.id),
            reach=r.reach,
            impact=r.impact,
            confidence=r.confidence,
            effort=r.effort,
            calculated_score=r.calculated_score,
        )

    @strawberry.field
    def comments(self, info: Info) -> list[CommentType]:
        items = info.context["clients"].hypothesis.list_comments("HYPOTHESIS", str(self.id))
        return [
            CommentType(
                id=strawberry.ID(c.id),
                entity_type=CommentEntityType(c.entity_type),
                entity_id=strawberry.ID(c.entity_id),
                text=c.text,
                created_at=c.created_at,
                author_id=c.author_id,
            )
            for c in items
        ]

    @strawberry.field
    def backlog_task(self, info: Info) -> Optional[BacklogTaskType]:
        bt = info.context["clients"].integration.get_backlog_task(str(self.id))
        if not bt:
            return None
        return BacklogTaskType(
            id=strawberry.ID(bt.id),
            hypothesis_id=strawberry.ID(bt.hypothesis_id),
            external_system=bt.external_system,
            external_key=bt.external_key,
            external_url=bt.external_url,
            status=bt.status,
            synced_at=bt.synced_at,
        )


@strawberry.type
class ResearchDesignType:
    id: strawberry.ID
    goal: str
    questions: str
    success_criteria: str
    user_stories: Optional[str]


@strawberry.type
class InsightType:
    id: strawberry.ID
    text: str
    created_at: str
    created_by: strawberry.Private[str]

    @strawberry.field
    def author(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.created_by)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )


@strawberry.type
class ResearchNoteType:
    id: strawberry.ID
    text: str
    created_at: str
    author_id: strawberry.Private[str]

    @strawberry.field
    def author(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.author_id)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )


@strawberry.type
class ReportType:
    id: strawberry.ID
    research_id: strawberry.ID
    conclusion: str
    recommendations: str
    file_url: Optional[str]
    created_at: str


@strawberry.type
class ResearchType:
    id: strawberry.ID
    title: str
    status: ResearchStatus
    type: str
    method: str
    target_audience: str
    sample_size: int
    start_date: Optional[str]
    end_date: Optional[str]
    hypothesis_id: strawberry.Private[str]
    assignee_id: strawberry.Private[str]

    @strawberry.field
    def hypothesis(self, info: Info) -> HypothesisType:
        h = info.context["clients"].hypothesis.get_hypothesis(self.hypothesis_id)
        return HypothesisType(
            id=strawberry.ID(h.id),
            title=h.title,
            description=h.description,
            status=HypothesisStatus(h.status),
            priority=Priority(h.priority),
            created_at=h.created_at,
            product_id=h.product_id,
            owner_id=h.owner_id,
        )

    @strawberry.field
    def assignee(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.assignee_id)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )

    @strawberry.field
    def design(self, info: Info) -> Optional[ResearchDesignType]:
        d = info.context["clients"].research.get_design(str(self.id))
        if not d:
            return None
        return ResearchDesignType(
            id=strawberry.ID(d.id),
            goal=d.goal,
            questions=d.questions,
            success_criteria=d.success_criteria,
            user_stories=d.user_stories,
        )

    @strawberry.field
    def insights(self, info: Info) -> list[InsightType]:
        items = info.context["clients"].research.list_insights(str(self.id))
        return [
            InsightType(
                id=strawberry.ID(i.id),
                text=i.text,
                created_at=i.created_at,
                created_by=i.created_by,
            )
            for i in items
        ]

    @strawberry.field
    def notes(self, info: Info) -> list[ResearchNoteType]:
        items = info.context["clients"].research.list_notes(str(self.id))
        return [
            ResearchNoteType(
                id=strawberry.ID(n.id),
                text=n.text,
                created_at=n.created_at,
                author_id=n.author_id,
            )
            for n in items
        ]

    @strawberry.field
    def attachments(self, info: Info) -> list[AttachmentType]:
        items = info.context["clients"].file_storage.list_attachments("RESEARCH", str(self.id))
        return [
            AttachmentType(
                id=strawberry.ID(a.id),
                file_name=a.file_name,
                file_url=a.file_url,
                file_size=a.file_size,
            )
            for a in items
        ]

    @strawberry.field
    def report(self, info: Info) -> Optional[ReportType]:
        r = info.context["clients"].report.get_report_by_research(str(self.id))
        if not r:
            return None
        return ReportType(
            id=strawberry.ID(r.id),
            research_id=strawberry.ID(r.research_id),
            conclusion=r.conclusion,
            recommendations=r.recommendations,
            file_url=r.file_url,
            created_at=r.created_at,
        )


@strawberry.type
class RoadmapItemType:
    id: strawberry.ID
    hypothesis_id: strawberry.ID
    hypothesis_title: str
    start_date: str
    end_date: str
    duration: int
    dependencies: list[strawberry.ID]
    assignee_id: strawberry.Private[str]

    @strawberry.field
    def assignee(self, info: Info) -> UserType:
        u = info.context["clients"].user.get_user(self.assignee_id)
        return UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )


@strawberry.type
class DashboardMetricType:
    id: strawberry.ID
    metric_type: str
    product_id: strawberry.ID
    period: str
    value: float


@strawberry.type
class NotificationType:
    id: strawberry.ID
    type: str
    message: str
    entity_type: str
    entity_id: strawberry.ID
    is_read: bool
    created_at: str


@strawberry.type
class IdeaType:
    id: strawberry.ID
    product_id: strawberry.ID
    title: str
    description: str
    expected_effect: str
    category: str
    author_name: str
    status: str
    hypothesis_id: Optional[strawberry.ID]


@strawberry.type
class ActivityLogType:
    id: strawberry.ID
    entity_type: str
    entity_id: strawberry.ID
    user_id: strawberry.ID
    action: str
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: str


@strawberry.type
class StatusCountType:
    status: str
    count: int


@strawberry.type
class PriorityCountType:
    priority: str
    count: int


@strawberry.type
class HypothesesSummaryType:
    total_count: int
    by_status: list[StatusCountType]
    by_priority: list[PriorityCountType]
    avg_rice_score: Optional[float]
    max_rice_score: Optional[float]
    confirmed_rate: float
    in_backlog_count: int
