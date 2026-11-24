"""Централизованное структурированное логирование распределённой системы."""

from __future__ import annotations

from collections import deque
import logging
from typing import Deque


class InMemoryLogHandler(logging.Handler):
    def __init__(self, maxlen: int = 500) -> None:
        super().__init__()
        self.records: Deque[str] = deque(maxlen=maxlen)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


_memory_handler = InMemoryLogHandler()


def get_platform_logger(name: str = "pdp") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logging.getLogger("pdp").handlers:
        root_pdp = logging.getLogger("pdp")
        root_pdp.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        stream_h = logging.StreamHandler()
        stream_h.setFormatter(fmt)
        _memory_handler.setFormatter(fmt)
        root_pdp.addHandler(stream_h)
        root_pdp.addHandler(_memory_handler)
    return logger


def get_recent_logs(limit: int = 50) -> list[str]:
    items = list(_memory_handler.records)
    return items[-limit:]


def clear_recent_logs() -> None:
    _memory_handler.records.clear()
