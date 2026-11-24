"""Kafka Producer для публикации событий бизнес-сценариев."""

from __future__ import annotations

from collections import defaultdict
import os
from typing import Any, Callable, Optional

from kafka import KafkaProducer

from kafka_layer.events import build_envelope, deserialize_envelope, serialize_envelope


class LocalKafkaBroker:
    """Локальный брокер топиков Kafka с сериализацией байтов при отсутствии внешнего кластера."""

    def __init__(self) -> None:
        self._topics: dict[str, list[bytes]] = defaultdict(list)
        self._subscribers: dict[str, list[Callable[[bytes], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[bytes], None]) -> None:
        self._subscribers[topic].append(handler)

    def publish_raw(self, topic: str, raw: bytes) -> None:
        self._topics[topic].append(raw)
        for handler in self._subscribers.get(topic, []):
            handler(raw)

    def get_events(self, topic: str) -> list[dict[str, Any]]:
        return [deserialize_envelope(b).payload for b in self._topics.get(topic, [])]


class KafkaEventProducer:
    """Публикатор событий в Apache Kafka."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        local_broker: Optional[LocalKafkaBroker] = None,
    ) -> None:
        self._bootstrap = bootstrap_servers or os.environ.get("PDP_KAFKA_BOOTSTRAP_SERVERS", "")
        self._local_broker = local_broker or LocalKafkaBroker()
        self._producer: Optional[KafkaProducer] = None
        if self._bootstrap:
            try:
                self._producer = KafkaProducer(
                    bootstrap_servers=self._bootstrap,
                    request_timeout_ms=500,
                    max_block_ms=500,
                )
            except Exception:
                self._producer = None

    @property
    def broker(self) -> LocalKafkaBroker:
        return self._local_broker

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        envelope = build_envelope(topic, payload)
        raw = serialize_envelope(envelope)
        if self._producer is not None:
            self._producer.send(topic, value=raw)
            self._producer.flush(timeout=1.0)
        else:
            self._local_broker.publish_raw(topic, raw)

    def close(self) -> None:
        if self._producer is not None:
            self._producer.close()
