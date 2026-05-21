"""Contextualiser module for converting house state into natural-language context."""

from __future__ import annotations

from collections.abc import Iterable

from altinet.context.schemas import HouseState, Resident, Room


NIGHT_START_HOUR = 18


def build_context_block(house_state: HouseState, recent_events: Iterable[str] | None = None) -> str:
    """Convert a house state and recent events into a concise context paragraph."""
    sentences: list[str] = [f"The current time is {_format_time(house_state.current_time)}."]

    room_by_id = {room.id: room for room in house_state.rooms}
    for resident in house_state.residents:
        sentences.extend(_resident_context_sentences(resident, room_by_id, house_state))

    if recent_events:
        cleaned_events = [event.strip() for event in recent_events if event and event.strip()]
        if cleaned_events:
            sentences.append(f"Recent events: {'; '.join(cleaned_events)}.")

    return " ".join(sentences)


def _resident_context_sentences(
    resident: Resident, room_by_id: dict[str, Room], house_state: HouseState
) -> list[str]:
    sentences: list[str] = []

    if resident.current_room_id and resident.current_room_id in room_by_id:
        room = room_by_id[resident.current_room_id]
        room_name = room.name.lower()
        sentences.append(f"{resident.name} is in the {room_name}.")
        sentences.append(f"The {room_name} light is {'on' if room.light_on else 'off'}.")

        preference = _light_preference_for_room_at_night(resident, room)
        if preference and house_state.current_time.hour >= NIGHT_START_HOUR:
            sentences.append(
                f"{resident.name} usually prefers the {room_name} light {preference} at night."
            )
    else:
        sentences.append(f"{resident.name}'s current room is unknown.")

    return sentences


def _light_preference_for_room_at_night(resident: Resident, room: Room) -> str | None:
    preference_key = f"{room.id}_light_at_night"
    return resident.preferences.get(preference_key)


def _format_time(current_time) -> str:
    formatted = current_time.strftime("%I:%M %p")
    return formatted.lstrip("0")
