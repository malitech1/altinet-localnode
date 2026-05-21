from datetime import datetime, timezone

from altinet.context.contextualiser import build_context_block
from altinet.context.schemas import HouseState, Resident, Room


def test_build_context_block_includes_time_room_light_and_preference():
    house_state = HouseState(
        current_time=datetime(2026, 5, 21, 20, 0, tzinfo=timezone.utc),
        residents=[
            Resident(
                id="resident_elliot",
                name="Elliot",
                current_room_id="bedroom",
                preferences={"bedroom_light_at_night": "on"},
            )
        ],
        rooms=[Room(id="bedroom", name="Bedroom", light_on=False)],
    )

    result = build_context_block(house_state)

    assert "The current time is 8:00 PM." in result
    assert "Elliot is in the bedroom." in result
    assert "The bedroom light is off." in result
    assert "Elliot usually prefers the bedroom light on at night." in result


def test_build_context_block_includes_recent_events_when_provided():
    house_state = HouseState(current_time=datetime(2026, 5, 21, 10, 0, tzinfo=timezone.utc))

    result = build_context_block(house_state, recent_events=["Motion detected in hallway", "Door opened"])

    assert "Recent events: Motion detected in hallway; Door opened." in result
