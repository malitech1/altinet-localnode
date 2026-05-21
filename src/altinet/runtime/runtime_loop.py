"""Continuous LocalNode runtime loop."""

from __future__ import annotations

import json
import logging
import signal
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from altinet.context.contextualiser import build_context_block
from altinet.context.schemas import HouseState
from altinet.events.models import DeviceStateChanged, PersonEnteredRoom, PersonLeftRoom, TimeTick
from altinet.events.processor import EventProcessor
from altinet.events.queue import EventQueue
from altinet.memory import EpisodicMemory, MemoryContext, MemorySystem
from altinet.runtime.state_manager import RuntimeStateManager


@dataclass(slots=True)
class RuntimeStats:
    ticks: int = 0
    events_processed: int = 0
    decisions_made: int = 0
    loop_errors: int = 0
    started_at: datetime | None = None
    last_tick_at: datetime | None = None


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "time": datetime.now(timezone.utc).isoformat(),
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if hasattr(record, "stats"):
            payload["stats"] = record.stats
        if hasattr(record, "decision"):
            payload["decision"] = record.decision
        if hasattr(record, "context"):
            payload["context"] = record.context
        return json.dumps(payload)


def configure_runtime_logger() -> logging.Logger:
    logger = logging.getLogger("altinet.runtime")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
    return logger


class RuntimeLoop:
    def __init__(self, house_state: HouseState, tick_rate_hz: float = 1.0) -> None:
        if tick_rate_hz <= 0:
            raise ValueError("tick_rate_hz must be positive")

        self.house_state = house_state
        self.tick_rate_hz = tick_rate_hz
        self.event_queue = EventQueue()
        self.processor = EventProcessor()
        self.memory = MemorySystem()
        self.runtime_state_manager = RuntimeStateManager()
        self.stats = RuntimeStats(started_at=datetime.now(timezone.utc))
        self._stop_requested = False
        self.logger = configure_runtime_logger()

    def run(self, max_ticks: int | None = None) -> RuntimeStats:
        self._install_signal_handlers()
        tick_interval = 1.0 / self.tick_rate_hz

        while not self._stop_requested:
            if max_ticks is not None and self.stats.ticks >= max_ticks:
                break

            tick_started = time.monotonic()
            try:
                self._tick()
            except Exception as exc:  # broad on purpose for long-running loop resilience
                self.stats.loop_errors += 1
                self.logger.exception("runtime tick failed", extra={"event": {"error": str(exc)}})

            elapsed = time.monotonic() - tick_started
            time.sleep(max(0.0, tick_interval - elapsed))

        self.logger.info(
            "runtime loop stopped",
            extra={"stats": self._stats_payload()},
        )
        return self.stats

    def stop(self) -> None:
        self._stop_requested = True

    def _install_signal_handlers(self) -> None:
        def _handle_shutdown(_signum, _frame):
            self.logger.info("shutdown signal received")
            self.stop()

        signal.signal(signal.SIGINT, _handle_shutdown)
        signal.signal(signal.SIGTERM, _handle_shutdown)

    def _tick(self) -> None:
        self.stats.ticks += 1
        now = self.house_state.current_time + timedelta(seconds=1 / self.tick_rate_hz)
        self.house_state.current_time = now
        self.stats.last_tick_at = now

        generated_events = self._generate_simulation_events(now)
        for event in generated_events:
            self.event_queue.push(event)

        processed_count = 0
        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            self.processor.process(self.house_state, event)
            self.runtime_state_manager.apply_event(event)
            processed_count += 1
        self.stats.events_processed += processed_count

        context = build_context_block(
            self.house_state,
            recent_events=[f"tick={self.stats.ticks}", f"events_processed={processed_count}"],
        )
        self.runtime_state_manager.set_inferred_context(context)

        retrieved_memories = self.memory.retrieve_relevant_memories(
            MemoryContext(
                current_time=self.house_state.current_time,
                residents=[resident.id for resident in self.house_state.residents],
                room=self.house_state.residents[0].current_room_id if self.house_state.residents else None,
                tags=["runtime", "lighting", "occupancy"],
            ),
            limit=3,
        )

        decision = self.processor.decide(self.house_state)
        self.stats.decisions_made += 1

        self.memory.add_memory(
            EpisodicMemory(
                event=f"Tick {self.stats.ticks}: {decision.explanation}",
                importance=0.6,
                timestamp=self.house_state.current_time,
                residents=[resident.id for resident in self.house_state.residents],
                rooms=[room.id for room in self.house_state.rooms if room.occupied_by_resident_ids],
                tags=["decision", decision.selected_action.value],
            )
        )

        self.logger.info(
            "runtime tick complete",
            extra={
                "event": {"tick": self.stats.ticks, "generated_events": len(generated_events)},
                "context": context,
                "decision": decision.model_dump(mode="json"),
                "stats": self._stats_payload(),
            },
        )

        if retrieved_memories:
            self.logger.info(
                "memory retrieval",
                extra={"event": {"top_memory": retrieved_memories[0].event, "count": len(retrieved_memories)}},
            )

    def _generate_simulation_events(self, now: datetime) -> list:
        events = [TimeTick(timestamp=now, source="runtime", confidence=1.0, metadata={"tick": str(self.stats.ticks)})]

        if self.house_state.residents and self.house_state.rooms:
            resident = self.house_state.residents[0]
            rooms = self.house_state.rooms
            if len(rooms) > 1 and self.stats.ticks % 2 == 0:
                current_index = next((i for i, room in enumerate(rooms) if room.id == resident.current_room_id), 0)
                next_room = rooms[(current_index + 1) % len(rooms)]
                if resident.current_room_id:
                    events.append(PersonLeftRoom(timestamp=now, source="runtime", confidence=0.95, person_id=resident.id, room_id=resident.current_room_id))
                events.append(PersonEnteredRoom(timestamp=now, source="runtime", confidence=0.95, person_id=resident.id, room_id=next_room.id))

            occupied_room = next((r for r in rooms if r.occupied_by_resident_ids), None)
            if occupied_room and self.stats.ticks % 3 == 0:
                device = next((d for d in self.house_state.devices if d.room_id == occupied_room.id and d.device_type == "light"), None)
                if device:
                    events.append(
                        DeviceStateChanged(
                            timestamp=now,
                            source="runtime",
                            confidence=0.93,
                            device_id=device.id,
                            is_on=not device.is_on,
                            metadata={"reason": "runtime_light_simulation"},
                        )
                    )
        return events

    def _stats_payload(self) -> dict[str, object]:
        return {
            "ticks": self.stats.ticks,
            "events_processed": self.stats.events_processed,
            "decisions_made": self.stats.decisions_made,
            "loop_errors": self.stats.loop_errors,
            "started_at": self.stats.started_at.isoformat() if self.stats.started_at else None,
            "last_tick_at": self.stats.last_tick_at.isoformat() if self.stats.last_tick_at else None,
        }


def run_runtime_loop(sample_path: Path, tick_rate_hz: float = 1.0, max_ticks: int | None = None) -> RuntimeStats:
    house_state = HouseState.model_validate_json(sample_path.read_text(encoding="utf-8"))
    loop = RuntimeLoop(house_state=house_state, tick_rate_hz=tick_rate_hz)
    return loop.run(max_ticks=max_ticks)
