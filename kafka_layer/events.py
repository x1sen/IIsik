"""Топики Kafka и конверт сообщений (payload)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from typing import Any
import uuid


TOPIC_HYPOTHESIS_CREATED = "HypothesisCreated"
TOPIC_HYPOTHESIS_PRIORITIZED = "HypothesisPrioritized"
TOPIC_HYPOTHESIS_VALIDATED = "HypothesisValidated"
TOPIC_HYPOTHESIS_EXPORTED = "HypothesisExported"
TOPIC_BACKLOG_TASK_CREATED = "BacklogTaskCreated"
TOPIC_COMMENT_ADDED = "CommentAdded"
TOPIC_RESEARCH_CREATED = "ResearchCreated"
TOPIC_RESEARCH_COMPLETED = "ResearchCompleted"
TOPIC_REPORT_READY = "ReportReady"
TOPIC_ROADMAP_ITEM_CREATED = "RoadmapItemCreated"
TOPIC_IDEA_SUBMITTED = "IdeaSubmitted"


@dataclass(frozen=True)
class KafkaEventEnvelope:
    event_id: str
    event_type: str
    timestamp: str
    payload: dict[str, Any]


def build_envelope(event_type: str, payload: dict[str, Any]) -> KafkaEventEnvelope:
    return KafkaEventEnvelope(
        event_id=uuid.uuid4().hex,
        event_type=event_type,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        payload=payload,
    )


def serialize_envelope(envelope: KafkaEventEnvelope) -> bytes:
    return json.dumps(asdict(envelope), ensure_ascii=False).encode("utf-8")


def deserialize_envelope(raw: bytes) -> KafkaEventEnvelope:
    data = json.loads(raw.decode("utf-8"))
    return KafkaEventEnvelope(
        event_id=data["event_id"],
        event_type=data["event_type"],
        timestamp=data["timestamp"],
        payload=data["payload"],
    )
