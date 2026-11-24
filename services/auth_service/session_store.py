"""Хранилище активных сессий в Redis (с TTL и fallback на fakeredis при отсутствии локального сервера)."""

from __future__ import annotations

import json
from typing import Any, Optional

import fakeredis
import redis


def create_redis_client(redis_url: str) -> Any:
    """Создаёт клиент Redis; если локальный сервер Redis недоступен, использует fakeredis."""
    try:
        client = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=0.3)
        client.ping()
        return client
    except Exception:
        return fakeredis.FakeRedis(decode_responses=True)


class RedisSessionStore:
    """Управление активными пользовательскими сессиями в Redis с ограничением времени жизни (TTL)."""

    def __init__(self, client: Any) -> None:
        self._client = client

    @staticmethod
    def _key(session_id: str) -> str:
        return f"session:{session_id}"

    def create_session(self, session_id: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        self._client.setex(self._key(session_id), ttl_seconds, json.dumps(payload))

    def get_session(self, session_id: str) -> Optional[dict[str, Any]]:
        raw = self._client.get(self._key(session_id))
        if raw is None:
            return None
        return json.loads(raw)

    def delete_session(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))

    def get_ttl(self, session_id: str) -> int:
        return int(self._client.ttl(self._key(session_id)))
