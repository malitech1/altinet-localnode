"""Event processor that mutates HouseState over time."""

from __future__ import annotations

from altinet.context.contextualiser import build_context_block
from altinet.context.schemas import HouseState
from altinet.decision.mock_engine import MockDecision, decide_action
from altinet.events.models import (
    AltinetEvent,
    DeviceStateChanged,
    MotionDetected,
    PersonEnteredRoom,
    PersonLeftRoom,
    TimeTick,
)


class EventProcessor:
    def process(self, house_state: HouseState, event: AltinetEvent) -> HouseState:
        if isinstance(event, PersonEnteredRoom):
            self._person_entered_room(house_state, event.person_id, event.room_id)
        elif isinstance(event, PersonLeftRoom):
            self._person_left_room(house_state, event.person_id, event.room_id)
        elif isinstance(event, DeviceStateChanged):
            self._device_state_changed(house_state, event.device_id, event.is_on)
        elif isinstance(event, MotionDetected):
            pass
        elif isinstance(event, TimeTick):
            pass

        house_state.current_time = event.timestamp
        return house_state

    def process_all(self, house_state: HouseState, event_queue) -> HouseState:
        while not event_queue.is_empty():
            self.process(house_state, event_queue.pop())
        return house_state

    def contextualise(self, house_state: HouseState, events: list[str]) -> str:
        return build_context_block(house_state, recent_events=events)

    def decide(self, house_state: HouseState) -> MockDecision:
        return decide_action(house_state)

    def _person_entered_room(self, house_state: HouseState, person_id: str, room_id: str) -> None:
        for resident in house_state.residents:
            if resident.id == person_id:
                resident.current_room_id = room_id

        for room in house_state.rooms:
            if room.id == room_id and person_id not in room.occupied_by_resident_ids:
                room.occupied_by_resident_ids.append(person_id)
            elif room.id != room_id and person_id in room.occupied_by_resident_ids:
                room.occupied_by_resident_ids.remove(person_id)

    def _person_left_room(self, house_state: HouseState, person_id: str, room_id: str) -> None:
        for resident in house_state.residents:
            if resident.id == person_id and resident.current_room_id == room_id:
                resident.current_room_id = None

        for room in house_state.rooms:
            if room.id == room_id and person_id in room.occupied_by_resident_ids:
                room.occupied_by_resident_ids.remove(person_id)

    def _device_state_changed(self, house_state: HouseState, device_id: str, is_on: bool) -> None:
        room_id: str | None = None
        for device in house_state.devices:
            if device.id == device_id:
                device.is_on = is_on
                room_id = device.room_id

        if room_id is None:
            return

        for room in house_state.rooms:
            if room.id == room_id:
                room.light_on = is_on
