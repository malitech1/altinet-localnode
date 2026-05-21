from datetime import datetime, timezone

from altinet.context.schemas import Device, HouseState, Resident, Room
from altinet.events.models import DeviceStateChanged, PersonEnteredRoom
from altinet.events.processor import EventProcessor
from altinet.events.queue import EventQueue


def _house_state() -> HouseState:
    return HouseState(
        current_time=datetime(2026, 5, 21, 19, 0, tzinfo=timezone.utc),
        residents=[
            Resident(
                id="resident_elliot",
                name="Elliot",
                current_room_id=None,
                preferences={"bedroom_light_at_night": "on"},
            )
        ],
        rooms=[Room(id="bedroom", name="Bedroom", occupied_by_resident_ids=[], light_on=False)],
        devices=[Device(id="bedroom_light", room_id="bedroom", device_type="light", is_on=False)],
    )


def test_event_queue_and_processor_update_house_state():
    state = _house_state()
    queue = EventQueue()
    processor = EventProcessor()

    t = datetime(2026, 5, 21, 20, 0, tzinfo=timezone.utc)
    queue.push(
        PersonEnteredRoom(
            timestamp=t,
            source="unit-test",
            confidence=0.99,
            person_id="resident_elliot",
            room_id="bedroom",
            metadata={"path": "hallway"},
        )
    )
    queue.push(
        DeviceStateChanged(
            timestamp=t,
            source="unit-test",
            confidence=0.95,
            device_id="bedroom_light",
            is_on=True,
            metadata={"reason": "manual"},
        )
    )

    processor.process_all(state, queue)

    assert state.residents[0].current_room_id == "bedroom"
    assert "resident_elliot" in state.rooms[0].occupied_by_resident_ids
    assert state.rooms[0].light_on is True


def test_event_processor_contextualises_and_decides():
    state = _house_state()
    processor = EventProcessor()

    processor.process(
        state,
        PersonEnteredRoom(
            timestamp=datetime(2026, 5, 21, 20, 0, tzinfo=timezone.utc),
            source="unit-test",
            confidence=0.99,
            person_id="resident_elliot",
            room_id="bedroom",
            metadata={},
        ),
    )

    context = processor.contextualise(state, events=["Elliot entered bedroom"])
    decision = processor.decide(state)

    assert "Elliot is in the bedroom." in context
    assert decision.selected_action == "turn_light_on"
