"""Runtime state manager for continuously updated house state."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from altinet.events.models import (
    AltinetEvent,
    AudioDetected,
    DeviceStateChanged,
    MotionDetected,
    PersonEnteredRoom,
    PersonLeftRoom,
    TimeTick,
)


class RuntimeState(BaseModel):
    current_room_occupancy: dict[str, list[str]] = Field(default_factory=dict)
    devices: dict[str, dict[str, object]] = Field(default_factory=dict)
    recent_events: list[dict[str, object]] = Field(default_factory=list)
    active_residents: list[str] = Field(default_factory=list)
    current_inferred_context: str | None = None
    timestamps: dict[str, datetime] = Field(default_factory=dict)


class RuntimeStateManager:
    def __init__(self, state_path: str | Path = "data/runtime/runtime_state.json") -> None:
        self.state_path = Path(state_path)
        self.state = self.restore_or_create()

    def restore_or_create(self) -> RuntimeState:
        if self.state_path.exists():
            return RuntimeState.model_validate_json(self.state_path.read_text(encoding="utf-8"))
        return RuntimeState()

    def save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(self.state.model_dump_json(indent=2), encoding="utf-8")

    def apply_event(self, event: AltinetEvent) -> RuntimeState:
        self._record_event(event)

        if isinstance(event, PersonEnteredRoom):
            self._enter_room(event.person_id, event.room_id)
        elif isinstance(event, PersonLeftRoom):
            self._leave_room(event.person_id, event.room_id)
        elif isinstance(event, DeviceStateChanged):
            self._device_state_changed(event.device_id, event.is_on, event.metadata)
        elif isinstance(event, MotionDetected):
            self.state.timestamps[f"motion:{event.room_id}"] = event.timestamp
        elif isinstance(event, AudioDetected):
            self.state.timestamps[f"audio:{event.room_id}"] = event.timestamp
        elif isinstance(event, TimeTick):
            self.state.timestamps["last_tick"] = event.timestamp

        self.state.timestamps["last_event"] = event.timestamp
        self.save()
        return self.state

    def set_inferred_context(self, context: str) -> None:
        self.state.current_inferred_context = context
        self.state.timestamps["context_updated_at"] = datetime.now(timezone.utc)
        self.save()

    def _record_event(self, event: AltinetEvent) -> None:
        event_payload = event.model_dump(mode="json")
        self.state.recent_events.append({"type": event.__class__.__name__, **event_payload})
        self.state.recent_events = self.state.recent_events[-100:]

    def _enter_room(self, person_id: str, room_id: str) -> None:
        for residents in self.state.current_room_occupancy.values():
            if person_id in residents:
                residents.remove(person_id)

        room_residents = self.state.current_room_occupancy.setdefault(room_id, [])
        if person_id not in room_residents:
            room_residents.append(person_id)

        if person_id not in self.state.active_residents:
            self.state.active_residents.append(person_id)

    def _leave_room(self, person_id: str, room_id: str) -> None:
        room_residents = self.state.current_room_occupancy.get(room_id, [])
        if person_id in room_residents:
            room_residents.remove(person_id)

        still_present = any(person_id in residents for residents in self.state.current_room_occupancy.values())
        if not still_present and person_id in self.state.active_residents:
            self.state.active_residents.remove(person_id)

    def _device_state_changed(self, device_id: str, is_on: bool, metadata: dict[str, str]) -> None:
        device_state = self.state.devices.setdefault(device_id, {})
        device_state["is_on"] = is_on
        if metadata:
            device_state["metadata"] = metadata
