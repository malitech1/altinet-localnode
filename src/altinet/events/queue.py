"""FIFO queue for Altinet events."""

from __future__ import annotations

from collections import deque

from altinet.events.models import AltinetEvent


class EventQueue:
    def __init__(self) -> None:
        self._queue: deque[AltinetEvent] = deque()

    def push(self, event: AltinetEvent) -> None:
        self._queue.append(event)

    def pop(self) -> AltinetEvent:
        return self._queue.popleft()

    def is_empty(self) -> bool:
        return not self._queue

    def __len__(self) -> int:
        return len(self._queue)
