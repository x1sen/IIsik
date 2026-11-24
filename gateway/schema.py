"""GraphQL Schema (Query для получения данных)."""

import strawberry

from gateway.resolvers import (
    resolve_activity_logs,
    resolve_dashboard_metrics,
    resolve_find_duplicate_hypotheses,
    resolve_hypotheses,
    resolve_hypothesis,
    resolve_ideas,
    resolve_my_notifications,
    resolve_product,
    resolve_products,
    resolve_research,
    resolve_researches,
    resolve_roadmap,
    resolve_users,
)
from gateway.types import (
    ActivityLogType,
    DashboardMetricType,
    DuplicateCandidateType,
    HypothesisType,
    IdeaType,
    NotificationType,
    ProductType,
    ResearchType,
    RoadmapItemType,
    UserType,
)


@strawberry.type
class Query:
    hypothesis: HypothesisType = strawberry.field(resolver=resolve_hypothesis)
    hypotheses: list[HypothesisType] = strawberry.field(resolver=resolve_hypotheses)
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


schema = strawberry.Schema(query=Query)
