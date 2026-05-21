"""Local deterministic mock decision engine for pipeline testing."""

from __future__ import annotations

from pydantic import BaseModel

from altinet.context.contextualiser import NIGHT_START_HOUR
from altinet.context.schemas import HouseState, PossibleAction, Resident, Room


class MockDecision(BaseModel):
    selected_action: PossibleAction
    explanation: str
    confidence: float


def decide_action(house_state: HouseState) -> MockDecision:
    """Choose an action using simple deterministic rules."""
    room_by_id = {room.id: room for room in house_state.rooms}

    for resident in house_state.residents:
        room = _room_for_resident(resident, room_by_id)
        if room is None:
            continue

        if not _room_has_occupant(room):
            continue

        if room.light_on:
            return MockDecision(
                selected_action=PossibleAction.DO_NOTHING,
                explanation=(
                    f"{resident.name} is in the {room.name.lower()}, but the light is already on."
                ),
                confidence=0.99,
            )

        if _is_night(house_state) and _prefers_lights_on_at_night(resident, room):
            return MockDecision(
                selected_action=PossibleAction.TURN_LIGHT_ON,
                explanation=(
                    f"It is night and {resident.name} prefers the {room.name.lower()} light on."
                ),
                confidence=0.96,
            )

        return MockDecision(
            selected_action=PossibleAction.DO_NOTHING,
            explanation=(
                f"{resident.name} is in the {room.name.lower()}, but no rule requires changing lights."
            ),
            confidence=0.8,
        )

    return MockDecision(
        selected_action=PossibleAction.DO_NOTHING,
        explanation="No occupied room needs a lighting change.",
        confidence=0.95,
    )


def _room_for_resident(resident: Resident, room_by_id: dict[str, Room]) -> Room | None:
    if resident.current_room_id is None:
        return None
    return room_by_id.get(resident.current_room_id)


def _room_has_occupant(room: Room) -> bool:
    return bool(room.occupied_by_resident_ids or room.occupied_by_pet_ids)


def _is_night(house_state: HouseState) -> bool:
    return house_state.current_time.hour >= NIGHT_START_HOUR


def _prefers_lights_on_at_night(resident: Resident, room: Room) -> bool:
    preference_key = f"{room.id}_light_at_night"
    return resident.preferences.get(preference_key) == "on"
