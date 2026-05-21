"""Episodic memory storage and retrieval for Altinet."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable


@dataclass(slots=True)
class EpisodicMemory:
    """Represents a meaningful event in Altinet memory."""

    event: str
    importance: float
    timestamp: datetime
    residents: list[str] = field(default_factory=list)
    rooms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MemoryContext:
    """Current context used for memory retrieval scoring."""

    current_time: datetime
    residents: list[str] = field(default_factory=list)
    room: str | None = None
    tags: list[str] = field(default_factory=list)


class MemorySystem:
    """Stores episodic memories and retrieves relevant ones."""

    def __init__(self) -> None:
        self._episodic_memories: list[EpisodicMemory] = []

    @property
    def episodic_memories(self) -> list[EpisodicMemory]:
        return list(self._episodic_memories)

    def add_memory(self, memory: EpisodicMemory) -> None:
        self._episodic_memories.append(memory)

    def retrieve_relevant_memories(self, current_context: MemoryContext, limit: int = 5) -> list[EpisodicMemory]:
        scored = sorted(
            self._episodic_memories,
            key=lambda memory: self._score_memory(memory, current_context),
            reverse=True,
        )
        return scored[:limit]

    def _score_memory(self, memory: EpisodicMemory, context: MemoryContext) -> float:
        room_score = 2.0 if context.room and context.room in memory.rooms else 0.0
        resident_overlap = _overlap_count(memory.residents, context.residents)
        resident_score = resident_overlap * 1.5
        tag_overlap = _overlap_count(memory.tags, context.tags)
        tag_score = tag_overlap * 1.0
        time_score = _time_similarity(memory.timestamp, context.current_time)

        return memory.importance + room_score + resident_score + tag_score + time_score


def _overlap_count(a: Iterable[str], b: Iterable[str]) -> int:
    return len(set(a).intersection(set(b)))


def _time_similarity(a: datetime, b: datetime) -> float:
    hour_delta = abs(a.hour - b.hour)
    wrapped_delta = min(hour_delta, 24 - hour_delta)
    return max(0.0, 2.0 - (wrapped_delta / 6.0))
