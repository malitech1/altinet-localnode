from datetime import datetime

import pytest
from pydantic import ValidationError

from altinet.context.schemas import (
    DecisionRequest,
    DecisionResponse,
    Device,
    HouseState,
    Pet,
    PossibleAction,
    Resident,
    Room,
    SensorReading,
)


def test_house_state_supports_multiple_residents_and_pets():
    house_state = HouseState(
        residents=[
            Resident(id="resident_1", name="Elliot", current_room_id="bedroom"),
            Resident(id="resident_2", name="Noa", current_room_id="kitchen"),
        ],
        pets=[Pet(id="pet_1", name="Milo", species="cat", current_room_id="bedroom")],
        rooms=[
            Room(
                id="bedroom",
                name="Bedroom",
                occupied_by_resident_ids=["resident_1"],
                occupied_by_pet_ids=["pet_1"],
                light_on=False,
            ),
            Room(
                id="kitchen",
                name="Kitchen",
                occupied_by_resident_ids=["resident_2"],
                light_on=True,
            ),
        ],
        devices=[Device(id="bedroom_light", room_id="bedroom", device_type="light", is_on=False)],
        sensor_readings=[
            SensorReading(
                sensor_id="bedroom_motion",
                room_id="bedroom",
                metric="motion",
                value=1,
                unit="bool",
                recorded_at=datetime.fromisoformat("2026-05-21T20:00:00+00:00"),
            )
        ],
        current_time=datetime.fromisoformat("2026-05-21T20:00:00+00:00"),
        user_preferences={"elliot:bedroom_light_at_night": "on"},
    )

    assert len(house_state.residents) == 2
    assert len(house_state.pets) == 1
    assert house_state.rooms[0].light_on is False


def test_decision_request_and_response_validate_actions():
    house_state = HouseState(current_time=datetime.fromisoformat("2026-05-21T20:00:00+00:00"))
    request = DecisionRequest(
        house_state=house_state,
        possible_actions=[
            PossibleAction.TURN_LIGHT_ON,
            PossibleAction.TURN_LIGHT_OFF,
            PossibleAction.DO_NOTHING,
        ],
    )

    response = DecisionResponse(
        selected_action=PossibleAction.TURN_LIGHT_ON,
        rationale="Resident entered a dark bedroom at night.",
    )

    assert request.possible_actions[0] == "turn_light_on"
    assert response.selected_action == "turn_light_on"


def test_invalid_action_fails_validation():
    house_state = HouseState(current_time=datetime.fromisoformat("2026-05-21T20:00:00+00:00"))

    with pytest.raises(ValidationError):
        DecisionRequest(house_state=house_state, possible_actions=["open_window"])
