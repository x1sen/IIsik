"""Кеширование часто используемых данных в Redis."""

from __future__ import annotations

import json
from typing import Any, Optional

from shared.logging_config import get_platform_logger

_log = get_platform_logger("pdp.cache")


class RedisCache:
    def __init__(self, client: Any, default_ttl_seconds: int = 300) -> None:
        self._client = client
        self._ttl = default_ttl_seconds

    def get_json(self, key: str) -> Optional[Any]:
        try:
            raw = self._client.get(key)
        except Exception as exc:
            _log.warning("REDIS CACHE ERROR on GET %s: %s", key, exc)
            return None
        if raw is None:
            _log.info("CACHE MISS key=%s", key)
            return None
        _log.info("CACHE HIT key=%s", key)
        return json.loads(raw)

    def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl
        try:
            self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            _log.info("CACHE SET key=%s ttl=%ss", key, ttl)
        except Exception as exc:
            _log.warning("REDIS CACHE ERROR on SET %s: %s", key, exc)

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
            _log.info("CACHE INVALIDATE key=%s", key)
        except Exception as exc:
            _log.warning("REDIS CACHE ERROR on DELETE %s: %s", key, exc)

    def invalidate_prefix(self, prefix: str) -> None:
        try:
            keys = list(self._client.scan_iter(match=f"{prefix}*"))
            if keys:
                self._client.delete(*keys)
                _log.info("CACHE INVALIDATE prefix=%s count=%d", prefix, len(keys))
        except Exception as exc:
            _log.warning("REDIS CACHE ERROR on INVALIDATE %s*: %s", prefix, exc)
