"""Доменные модели Hypothesis Service."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HypothesisModel:
    id: str
    title: str
    description: str
    status: str
    priority: str
    rice_score: Optional[float]
    product_id: str
    owner_id: str
    created_at: str


@dataclass(frozen=True)
class HypothesisTemplateModel:
    id: str
    hypothesis_id: str
    if_action: str
    then_result: str
    because_assumption: str


@dataclass(frozen=True)
class RICEScoreModel:
    id: str
    hypothesis_id: str
    reach: int
    impact: float
    confidence: float
    effort: int
    calculated_score: float


@dataclass(frozen=True)
class CommentModel:
    id: str
    entity_type: str
    entity_id: str
    author_id: str
    text: str
    created_at: str


@dataclass(frozen=True)
class DuplicateCandidateModel:
    hypothesis_id: str
    title: str
    similarity: float
    status: str


@dataclass(frozen=True)
class StatusCountModel:
    status: str
    count: int


@dataclass(frozen=True)
class PriorityCountModel:
    priority: str
    count: int


@dataclass(frozen=True)
class HypothesesSummaryModel:
    total_count: int
    by_status: list[StatusCountModel]
    by_priority: list[PriorityCountModel]
    avg_rice_score: Optional[float]
    max_rice_score: Optional[float]
    confirmed_rate: float
    in_backlog_count: int
