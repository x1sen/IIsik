"""GraphQL Schema (Query и Mutation с защитой JWT, Redis-сессиями и RBAC)."""

import strawberry

from gateway.resolvers import (
    resolve_activity_logs,
    resolve_add_comment,
    resolve_add_insight,
    resolve_add_research_note,
    resolve_apply_research_result,
    resolve_calculate_rice,
    resolve_create_hypothesis,
    resolve_create_research,
    resolve_dashboard_metrics,
    resolve_export_to_backlog,
    resolve_find_duplicate_hypotheses,
    resolve_hypotheses,
    resolve_hypotheses_summary,
    resolve_hypothesis,
    resolve_ideas,
    resolve_login,
    resolve_logout,
    resolve_mark_notification_read,
    resolve_me,
    resolve_my_notifications,
    resolve_product,
    resolve_products,
    resolve_publish_report,
    resolve_register,
    resolve_research,
    resolve_researches,
    resolve_roadmap,
    resolve_schedule_on_roadmap,
    resolve_submit_idea,
    resolve_users,
)
from gateway.types import (
    ActivityLogType,
    AuthPayloadType,
    AuthUserType,
    BacklogTaskType,
    CommentType,
    DashboardMetricType,
    DuplicateCandidateType,
    HypothesesSummaryType,
    HypothesisType,
    IdeaType,
    InsightType,
    NotificationType,
    ProductType,
    RICEScoreType,
    ReportType,
    ResearchNoteType,
    ResearchType,
    RoadmapItemType,
    UserType,
)


@strawberry.type
class Query:
    me: AuthUserType = strawberry.field(resolver=resolve_me)
    hypothesis: HypothesisType = strawberry.field(resolver=resolve_hypothesis)
    hypotheses: list[HypothesisType] = strawberry.field(resolver=resolve_hypotheses)
    hypotheses_summary: HypothesesSummaryType = strawberry.field(resolver=resolve_hypotheses_summary)
    find_duplicate_hypotheses: list[DuplicateCandidateType] = strawberry.field(
        resolver=resolve_find_duplicate_hypotheses
    )
    research: ResearchType = strawberry.field(resolver=resolve_research)
    researches: list[ResearchType] = strawberry.field(resolver=resolve_researches)
    roadmap: list[RoadmapItemType] = strawberry.field(resolver=resolve_roadmap)
    dashboard_metrics: list[DashboardMetricType] = strawberry.field(
        resolver=resolve_dashboard_metrics
    )
    my_notifications: list[NotificationType] = strawberry.field(
        resolver=resolve_my_notifications
    )
    product: ProductType = strawberry.field(resolver=resolve_product)
    products: list[ProductType] = strawberry.field(resolver=resolve_products)
    users: list[UserType] = strawberry.field(resolver=resolve_users)
    ideas: list[IdeaType] = strawberry.field(resolver=resolve_ideas)
    activity_logs: list[ActivityLogType] = strawberry.field(resolver=resolve_activity_logs)


@strawberry.type
class Mutation:
    register: AuthPayloadType = strawberry.field(resolver=resolve_register)
    login: AuthPayloadType = strawberry.field(resolver=resolve_login)
    logout: bool = strawberry.field(resolver=resolve_logout)
    create_hypothesis: HypothesisType = strawberry.field(resolver=resolve_create_hypothesis)
    calculate_rice: RICEScoreType = strawberry.field(
        name="calculateRICE", resolver=resolve_calculate_rice
    )
    apply_research_result: HypothesisType = strawberry.field(resolver=resolve_apply_research_result)
    export_to_backlog: BacklogTaskType = strawberry.field(resolver=resolve_export_to_backlog)
    create_research: ResearchType = strawberry.field(resolver=resolve_create_research)
    add_research_note: ResearchNoteType = strawberry.field(resolver=resolve_add_research_note)
    add_insight: InsightType = strawberry.field(resolver=resolve_add_insight)
    publish_report: ReportType = strawberry.field(resolver=resolve_publish_report)
    schedule_on_roadmap: RoadmapItemType = strawberry.field(resolver=resolve_schedule_on_roadmap)
    submit_idea: IdeaType = strawberry.field(resolver=resolve_submit_idea)
    add_comment: CommentType = strawberry.field(resolver=resolve_add_comment)
    mark_notification_read: NotificationType = strawberry.field(
        resolver=resolve_mark_notification_read
    )


schema = strawberry.Schema(query=Query, mutation=Mutation)
