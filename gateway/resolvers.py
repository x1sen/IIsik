"""Тонкие GraphQL-резолверы: только маршрутизация в клиенты сервисов и маппинг DTO."""

from __future__ import annotations

from typing import Optional

import strawberry
from strawberry.types import Info

from gateway.clients.mocks import ServiceClients
from gateway.types import (
    ActivityLogType,
    AddCommentInput,
    AddInsightInput,
    AddResearchNoteInput,
    ApplyResearchResultInput,
    BacklogTaskType,
    CalculateRICEInput,
    CommentType,
    CreateHypothesisInput,
    CreateReportInput,
    CreateResearchInput,
    CreateRoadmapItemInput,
    DashboardMetricType,
    DuplicateCandidateType,
    ExportToBacklogInput,
    FindDuplicatesInput,
    HypothesesSummaryType,
    HypothesisFilterInput,
    HypothesisSortInput,
    HypothesisStatus,
    HypothesisType,
    IdeaType,
    InsightType,
    NotificationType,
    Priority,
    PriorityCountType,
    ProductType,
    RICEScoreType,
    ReportType,
    ResearchFilterInput,
    ResearchNoteType,
    ResearchSortInput,
    ResearchStatus,
    ResearchType,
    RoadmapItemType,
    SortDirection,
    StatusCountType,
    SubmitIdeaInput,
    UserRole,
    UserType,
)
from services.business_operations import BusinessOperations


def _clients(info: Info) -> ServiceClients:
    return info.context["clients"]


def _ops(info: Info) -> BusinessOperations:
    return BusinessOperations(_clients(info))


def _map_hypothesis(h) -> HypothesisType:
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


def _map_research(r) -> ResearchType:
    return ResearchType(
        id=strawberry.ID(r.id),
        title=r.title,
        status=ResearchStatus(r.status),
        type=r.type,
        method=r.method,
        target_audience=r.target_audience,
        sample_size=r.sample_size,
        start_date=r.start_date,
        end_date=r.end_date,
        hypothesis_id=r.hypothesis_id,
        assignee_id=r.assignee_id,
    )


def resolve_hypothesis(info: Info, id: strawberry.ID) -> HypothesisType:
    h = _clients(info).hypothesis.get_hypothesis(str(id))
    return _map_hypothesis(h)


def resolve_hypotheses(
    info: Info,
    filter: Optional[HypothesisFilterInput] = None,
    sort: Optional[HypothesisSortInput] = None,
) -> list[HypothesisType]:
    items = _clients(info).hypothesis.list_hypotheses(
        product_id=str(filter.product_id) if filter and filter.product_id else None,
        status=filter.status.value if filter and filter.status else None,
        priority=filter.priority.value if filter and filter.priority else None,
        owner_id=str(filter.owner_id) if filter and filter.owner_id else None,
        min_rice_score=filter.min_rice_score if filter else None,
        search=filter.search if filter else None,
        sort_by=sort.field.value if sort else "created_at",
        sort_dir=sort.direction.value if sort else "DESC",
    )
    return [_map_hypothesis(h) for h in items]


def resolve_hypotheses_summary(
    info: Info, product_id: Optional[strawberry.ID] = None
) -> HypothesesSummaryType:
    s = _clients(info).hypothesis.get_summary(
        product_id=str(product_id) if product_id else None
    )
    return HypothesesSummaryType(
        total_count=s.total_count,
        by_status=[StatusCountType(status=x.status, count=x.count) for x in s.by_status],
        by_priority=[PriorityCountType(priority=x.priority, count=x.count) for x in s.by_priority],
        avg_rice_score=s.avg_rice_score,
        max_rice_score=s.max_rice_score,
        confirmed_rate=s.confirmed_rate,
        in_backlog_count=s.in_backlog_count,
    )


def resolve_find_duplicate_hypotheses(
    info: Info, input: FindDuplicatesInput
) -> list[DuplicateCandidateType]:
    items = _clients(info).hypothesis.find_duplicate_hypotheses(
        title=input.title,
        description=input.description,
        product_id=input.product_id,
    )
    return [
        DuplicateCandidateType(
            hypothesis_id=strawberry.ID(c.hypothesis_id),
            title=c.title,
            similarity=c.similarity,
            status=HypothesisStatus(c.status),
        )
        for c in items
    ]


def resolve_research(info: Info, id: strawberry.ID) -> ResearchType:
    r = _clients(info).research.get_research(str(id))
    return _map_research(r)


def resolve_researches(
    info: Info,
    filter: Optional[ResearchFilterInput] = None,
    sort: Optional[ResearchSortInput] = None,
) -> list[ResearchType]:
    items = _clients(info).research.list_researches(
        hypothesis_id=str(filter.hypothesis_id) if filter and filter.hypothesis_id else None,
        status=filter.status.value if filter and filter.status else None,
        assignee_id=str(filter.assignee_id) if filter and filter.assignee_id else None,
        sort_by=sort.field.value if sort else "start_date",
        sort_dir=sort.direction.value if sort else "DESC",
    )
    return [_map_research(r) for r in items]


def resolve_roadmap(
    info: Info, sort_direction: SortDirection = SortDirection.ASC
) -> list[RoadmapItemType]:
    items = _clients(info).roadmap.list_roadmap(sort_dir=sort_direction.value)
    return [
        RoadmapItemType(
            id=strawberry.ID(i.id),
            hypothesis_id=strawberry.ID(i.hypothesis_id),
            hypothesis_title=i.hypothesis_title,
            start_date=i.start_date,
            end_date=i.end_date,
            duration=i.duration,
            dependencies=[strawberry.ID(d) for d in i.dependencies],
            assignee_id=i.assignee_id,
        )
        for i in items
    ]


def resolve_dashboard_metrics(
    info: Info,
    product_id: Optional[strawberry.ID] = None,
    period: Optional[str] = None,
) -> list[DashboardMetricType]:
    items = _clients(info).analytics.get_dashboard_metrics(
        product_id=str(product_id) if product_id else None,
        period=period,
    )
    return [
        DashboardMetricType(
            id=strawberry.ID(m.id),
            metric_type=m.metric_type,
            product_id=strawberry.ID(m.product_id),
            period=m.period,
            value=m.value,
        )
        for m in items
    ]


def resolve_my_notifications(
    info: Info, user_id: strawberry.ID, unread_only: bool = False
) -> list[NotificationType]:
    items = _clients(info).notification.list_notifications(
        user_id=str(user_id), unread_only=unread_only
    )
    return [
        NotificationType(
            id=strawberry.ID(n.id),
            type=n.type,
            message=n.message,
            entity_type=n.entity_type,
            entity_id=strawberry.ID(n.entity_id),
            is_read=n.is_read,
            created_at=n.created_at,
        )
        for n in items
    ]


def resolve_products(info: Info) -> list[ProductType]:
    items = _clients(info).product.list_products()
    return [
        ProductType(
            id=strawberry.ID(p.id),
            name=p.name,
            category=p.category,
            status=p.status,
            description=p.description,
            owner_id=p.owner_id,
        )
        for p in items
    ]


def resolve_product(info: Info, id: strawberry.ID) -> ProductType:
    p = _clients(info).product.get_product(str(id))
    return ProductType(
        id=strawberry.ID(p.id),
        name=p.name,
        category=p.category,
        status=p.status,
        description=p.description,
        owner_id=p.owner_id,
    )


def resolve_users(info: Info) -> list[UserType]:
    items = _clients(info).user.list_users()
    return [
        UserType(
            id=strawberry.ID(u.id),
            name=u.name,
            email=u.email,
            role=UserRole(u.role),
            team_id=strawberry.ID(u.team_id) if u.team_id else None,
            expertise=u.expertise,
        )
        for u in items
    ]


def resolve_ideas(info: Info) -> list[IdeaType]:
    items = _clients(info).idea_portal.list_ideas()
    return [
        IdeaType(
            id=strawberry.ID(i.id),
            product_id=strawberry.ID(i.product_id),
            title=i.title,
            description=i.description,
            expected_effect=i.expected_effect,
            category=i.category,
            author_name=i.author_name,
            status=i.status,
            hypothesis_id=strawberry.ID(i.hypothesis_id) if i.hypothesis_id else None,
        )
        for i in items
    ]


def resolve_activity_logs(
    info: Info, entity_type: str, entity_id: strawberry.ID
) -> list[ActivityLogType]:
    items = _clients(info).audit.list_activity_logs(
        entity_type=entity_type, entity_id=str(entity_id)
    )
    return [
        ActivityLogType(
            id=strawberry.ID(l.id),
            entity_type=l.entity_type,
            entity_id=strawberry.ID(l.entity_id),
            user_id=strawberry.ID(l.user_id),
            action=l.action,
            old_value=l.old_value,
            new_value=l.new_value,
            timestamp=l.timestamp,
        )
        for l in items
    ]


def resolve_create_hypothesis(info: Info, input: CreateHypothesisInput) -> HypothesisType:
    h = _ops(info).create_hypothesis(
        title=input.title,
        description=input.description,
        product_id=str(input.product_id),
        owner_id=str(input.owner_id),
        priority=input.priority.value,
        if_action=input.if_action,
        then_result=input.then_result,
        because_assumption=input.because_assumption,
    )
    return _map_hypothesis(h)


def resolve_calculate_rice(info: Info, input: CalculateRICEInput) -> RICEScoreType:
    s = _ops(info).calculate_rice(
        hypothesis_id=str(input.hypothesis_id),
        reach=input.reach,
        impact=input.impact,
        confidence=input.confidence,
        effort=input.effort,
        user_id=str(input.user_id),
    )
    return RICEScoreType(
        id=strawberry.ID(s.id),
        reach=s.reach,
        impact=s.impact,
        confidence=s.confidence,
        effort=s.effort,
        calculated_score=s.calculated_score,
    )


def resolve_apply_research_result(info: Info, input: ApplyResearchResultInput) -> HypothesisType:
    h = _ops(info).apply_research_result(
        hypothesis_id=str(input.hypothesis_id),
        research_id=str(input.research_id),
        target_status=input.status.value,
        user_id=str(input.user_id),
    )
    return _map_hypothesis(h)


def resolve_export_to_backlog(info: Info, input: ExportToBacklogInput) -> BacklogTaskType:
    t = _ops(info).export_to_backlog(
        hypothesis_id=str(input.hypothesis_id),
        user_id=str(input.user_id),
    )
    return BacklogTaskType(
        id=strawberry.ID(t.id),
        hypothesis_id=strawberry.ID(t.hypothesis_id),
        external_system=t.external_system,
        external_key=t.external_key,
        external_url=t.external_url,
        status=t.status,
        synced_at=t.synced_at,
    )


def resolve_create_research(info: Info, input: CreateResearchInput) -> ResearchType:
    r = _ops(info).create_research(
        hypothesis_id=str(input.hypothesis_id),
        title=input.title,
        research_type=input.type,
        method=input.method,
        target_audience=input.target_audience,
        sample_size=input.sample_size,
        assignee_id=str(input.assignee_id),
        goal=input.goal,
        questions=input.questions,
        success_criteria=input.success_criteria,
        user_stories=input.user_stories,
    )
    return _map_research(r)


def resolve_add_research_note(info: Info, input: AddResearchNoteInput) -> ResearchNoteType:
    n = _ops(info).add_research_note(
        research_id=str(input.research_id),
        author_id=str(input.author_id),
        text=input.text,
    )
    return ResearchNoteType(
        id=strawberry.ID(n.id),
        text=n.text,
        created_at=n.created_at,
        author_id=n.author_id,
    )


def resolve_add_insight(info: Info, input: AddInsightInput) -> InsightType:
    ins = _ops(info).add_insight(
        research_id=str(input.research_id),
        created_by=str(input.created_by),
        text=input.text,
    )
    return InsightType(
        id=strawberry.ID(ins.id),
        text=ins.text,
        created_at=ins.created_at,
        created_by=ins.created_by,
    )


def resolve_publish_report(info: Info, input: CreateReportInput) -> ReportType:
    rep = _ops(info).publish_report(
        research_id=str(input.research_id),
        conclusion=input.conclusion,
        recommendations=input.recommendations,
        file_url=input.file_url,
        author_id=str(input.author_id),
    )
    return ReportType(
        id=strawberry.ID(rep.id),
        research_id=strawberry.ID(rep.research_id),
        conclusion=rep.conclusion,
        recommendations=rep.recommendations,
        file_url=rep.file_url,
        created_at=rep.created_at,
    )


def resolve_schedule_on_roadmap(info: Info, input: CreateRoadmapItemInput) -> RoadmapItemType:
    item = _ops(info).schedule_on_roadmap(
        hypothesis_id=str(input.hypothesis_id),
        start_date=input.start_date,
        end_date=input.end_date,
        dependencies=[str(d) for d in input.dependencies],
        assignee_id=str(input.assignee_id),
    )
    return RoadmapItemType(
        id=strawberry.ID(item.id),
        hypothesis_id=strawberry.ID(item.hypothesis_id),
        hypothesis_title=item.hypothesis_title,
        start_date=item.start_date,
        end_date=item.end_date,
        duration=item.duration,
        dependencies=[strawberry.ID(d) for d in item.dependencies],
        assignee_id=item.assignee_id,
    )


def resolve_submit_idea(info: Info, input: SubmitIdeaInput) -> IdeaType:
    idea = _ops(info).submit_idea(
        product_id=str(input.product_id),
        title=input.title,
        description=input.description,
        expected_effect=input.expected_effect,
        category=input.category,
        author_name=input.author_name,
        priority=input.priority.value,
        owner_id=str(input.owner_id) if input.owner_id else None,
        if_action=input.if_action,
        then_result=input.then_result,
        because_assumption=input.because_assumption,
    )
    return IdeaType(
        id=strawberry.ID(idea.id),
        product_id=strawberry.ID(idea.product_id),
        title=idea.title,
        description=idea.description,
        expected_effect=idea.expected_effect,
        category=idea.category,
        author_name=idea.author_name,
        status=idea.status,
        hypothesis_id=strawberry.ID(idea.hypothesis_id) if idea.hypothesis_id else None,
    )


def resolve_add_comment(info: Info, input: AddCommentInput) -> CommentType:
    c = _ops(info).add_comment(
        entity_type=input.entity_type.value,
        entity_id=str(input.entity_id),
        author_id=str(input.author_id),
        text=input.text,
    )
    return CommentType(
        id=strawberry.ID(c.id),
        entity_type=c.entity_type,
        entity_id=strawberry.ID(c.entity_id),
        text=c.text,
        created_at=c.created_at,
        author_id=c.author_id,
    )


def resolve_mark_notification_read(info: Info, id: strawberry.ID) -> NotificationType:
    n = _clients(info).notification.mark_read(str(id))
    return NotificationType(
        id=strawberry.ID(n.id),
        type=n.type,
        message=n.message,
        entity_type=n.entity_type,
        entity_id=strawberry.ID(n.entity_id),
        is_read=n.is_read,
        created_at=n.created_at,
    )
