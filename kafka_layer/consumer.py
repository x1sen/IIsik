"""Kafka Consumer: асинхронная обработка событий внутренними сервисами."""

from __future__ import annotations

from typing import Callable, Optional

from grpc_layer.server import ServiceRegistry
from kafka_layer.events import (
    TOPIC_BACKLOG_TASK_CREATED,
    TOPIC_COMMENT_ADDED,
    TOPIC_HYPOTHESIS_CREATED,
    TOPIC_HYPOTHESIS_EXPORTED,
    TOPIC_HYPOTHESIS_PRIORITIZED,
    TOPIC_HYPOTHESIS_VALIDATED,
    TOPIC_IDEA_SUBMITTED,
    TOPIC_REPORT_READY,
    TOPIC_RESEARCH_COMPLETED,
    TOPIC_RESEARCH_CREATED,
    TOPIC_ROADMAP_ITEM_CREATED,
    KafkaEventEnvelope,
    deserialize_envelope,
)
from kafka_layer.producer import LocalKafkaBroker
from shared.cache import RedisCache
from shared.logging_config import get_platform_logger

_log = get_platform_logger("pdp.kafka.consumer")


class KafkaEventConsumer:
    """Потребитель событий Kafka с логированием, обработкой ошибок и DLQ."""

    def __init__(self, broker: LocalKafkaBroker) -> None:
        self._broker = broker

    def register(self, topic: str, handler: Callable[[KafkaEventEnvelope], None]) -> None:
        def _on_message(raw: bytes) -> None:
            try:
                envelope = deserialize_envelope(raw)
            except Exception as exc:
                _log.error("KAFKA DESERIALIZE ERROR topic=%s error=%s", topic, exc)
                self._broker.dead_letter_queue.append(
                    {"topic": topic, "raw": raw.decode("utf-8", errors="replace"), "error": str(exc)}
                )
                return
            try:
                handler(envelope)
                _log.info("KAFKA CONSUME OK topic=%s event_id=%s", topic, envelope.event_id)
            except Exception as exc:
                _log.error(
                    "KAFKA CONSUME ERROR topic=%s event_id=%s error=%s",
                    topic,
                    envelope.event_id,
                    exc,
                )
                self._broker.dead_letter_queue.append(
                    {"topic": topic, "event_id": envelope.event_id, "error": str(exc)}
                )

        self._broker.subscribe(topic, _on_message)


def register_platform_consumers(
    registry: ServiceRegistry,
    broker: LocalKafkaBroker,
    cache: Optional[RedisCache] = None,
) -> KafkaEventConsumer:
    """Подписывает сервисы на события Kafka и инвалидирует кеш Redis при изменениях."""
    consumer = KafkaEventConsumer(broker)

    def _invalidate_analytics_cache() -> None:
        if cache is not None:
            cache.invalidate_prefix("cache:metrics:")
            cache.invalidate_prefix("cache:summary:")

    def on_hypothesis_created(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.analytics.handle_hypothesis_event(
            hypothesis_id=p["hypothesis_id"],
            product_id=p["product_id"],
            updated_at=env.timestamp,
            status="DRAFT",
            priority=p["priority"],
        )
        registry.roadmap.update_title_cache(p["hypothesis_id"], p["title"])
        registry.audit.record_action(
            "HYPOTHESIS", p["hypothesis_id"], p["owner_id"], "CREATED", None, "DRAFT"
        )
        registry.notification.create_notification(
            user_id=p.get("notify_user_id", p["owner_id"]),
            message=f"Создана новая гипотеза: {p['title']}",
            entity_type="HYPOTHESIS",
            entity_id=p["hypothesis_id"],
        )
        _invalidate_analytics_cache()

    def on_hypothesis_prioritized(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.analytics.handle_hypothesis_event(
            hypothesis_id=p["hypothesis_id"],
            product_id=p["product_id"],
            updated_at=env.timestamp,
            priority=p.get("priority"),
            rice_score=p["rice_score"],
        )
        registry.audit.record_action(
            "HYPOTHESIS",
            p["hypothesis_id"],
            p["user_id"],
            "PRIORITIZED",
            None,
            f"RICE={p['rice_score']}",
        )
        _invalidate_analytics_cache()

    def on_hypothesis_validated(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.analytics.handle_hypothesis_event(
            hypothesis_id=p["hypothesis_id"],
            product_id=p["product_id"],
            updated_at=env.timestamp,
            status=p["new_status"],
            priority=p.get("priority"),
        )
        registry.audit.record_action(
            "HYPOTHESIS",
            p["hypothesis_id"],
            p["user_id"],
            "VALIDATED",
            p["old_status"],
            p["new_status"],
        )
        registry.notification.create_notification(
            user_id=p["owner_id"],
            message=f"Гипотеза '{p['title']}' переведена в статус {p['new_status']} по итогам исследования",
            entity_type="HYPOTHESIS",
            entity_id=p["hypothesis_id"],
        )
        _invalidate_analytics_cache()

    def on_hypothesis_exported(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.analytics.handle_hypothesis_event(
            hypothesis_id=p["hypothesis_id"],
            product_id=p["product_id"],
            updated_at=env.timestamp,
            status="IN_BACKLOG",
        )
        registry.audit.record_action(
            "HYPOTHESIS", p["hypothesis_id"], p["exported_by"], "EXPORTED", "CONFIRMED", "IN_BACKLOG"
        )
        _invalidate_analytics_cache()

    def on_backlog_task_created(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.notification.create_notification(
            user_id=p["owner_id"],
            message=f"Гипотеза '{p['title']}' экспортирована в бэклог ({p['external_key']})",
            entity_type="HYPOTHESIS",
            entity_id=p["hypothesis_id"],
        )

    def on_research_created(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.audit.record_action(
            "RESEARCH", p["research_id"], p["assignee_id"], "CREATED", None, "PLANNED"
        )
        registry.notification.create_notification(
            user_id=p["assignee_id"],
            message=f"Назначено новое исследование: {p['title']}",
            entity_type="RESEARCH",
            entity_id=p["research_id"],
        )

    def on_research_completed(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.audit.record_action(
            "RESEARCH", p["research_id"], p["author_id"], "COMPLETED", "IN_PROGRESS", "REPORT_READY"
        )

    def on_report_ready(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.audit.record_action(
            "REPORT", p["report_id"], p["author_id"], "PUBLISHED", None, p["conclusion"]
        )
        registry.notification.create_notification(
            user_id=p["owner_id"],
            message=f"Опубликован отчёт по исследованию '{p['research_title']}'",
            entity_type="REPORT",
            entity_id=p["report_id"],
        )

    def on_roadmap_item_created(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.audit.record_action(
            "ROADMAP", p["roadmap_item_id"], p["assignee_id"], "SCHEDULED", None, f"{p['start_date']}..{p['end_date']}"
        )
        registry.notification.create_notification(
            user_id=p["assignee_id"],
            message=f"Гипотеза '{p['title']}' запланирована на дорожной карте ({p['start_date']} – {p['end_date']})",
            entity_type="HYPOTHESIS",
            entity_id=p["hypothesis_id"],
        )

    def on_idea_submitted(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.audit.record_action(
            "IDEA", p["idea_id"], p["owner_id"], "SUBMITTED", None, p["hypothesis_id"]
        )
        registry.notification.create_notification(
            user_id=p["notify_user_id"],
            message=f"Поступила новая идея '{p['title']}', создана гипотеза {p['hypothesis_id']}",
            entity_type="HYPOTHESIS",
            entity_id=p["hypothesis_id"],
        )

    def on_comment_added(env: KafkaEventEnvelope) -> None:
        p = env.payload
        registry.audit.record_action(
            p["entity_type"], p["entity_id"], p["author_id"], "COMMENTED", None, p["comment_id"]
        )

    consumer.register(TOPIC_HYPOTHESIS_CREATED, on_hypothesis_created)
    consumer.register(TOPIC_HYPOTHESIS_PRIORITIZED, on_hypothesis_prioritized)
    consumer.register(TOPIC_HYPOTHESIS_VALIDATED, on_hypothesis_validated)
    consumer.register(TOPIC_HYPOTHESIS_EXPORTED, on_hypothesis_exported)
    consumer.register(TOPIC_BACKLOG_TASK_CREATED, on_backlog_task_created)
    consumer.register(TOPIC_RESEARCH_CREATED, on_research_created)
    consumer.register(TOPIC_RESEARCH_COMPLETED, on_research_completed)
    consumer.register(TOPIC_REPORT_READY, on_report_ready)
    consumer.register(TOPIC_ROADMAP_ITEM_CREATED, on_roadmap_item_created)
    consumer.register(TOPIC_IDEA_SUBMITTED, on_idea_submitted)
    consumer.register(TOPIC_COMMENT_ADDED, on_comment_added)
    return consumer
