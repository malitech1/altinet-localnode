from datetime import datetime, timezone

from altinet.context.schemas import HouseState, PossibleAction, Resident, Room
from altinet.decision.prompt_builder import build_decision_prompt


def test_build_decision_prompt_contains_required_sections_and_json_shape():
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

    result = build_decision_prompt(
        house_state=house_state,
        possible_actions=[PossibleAction.TURN_LIGHT_ON, PossibleAction.DO_NOTHING],
        resident_background="Elliot wakes up early and prefers dim light transitions.",
        recent_events=["Bedroom motion detected"],
    )

    assert "# System Role" in result
    assert "# House Rules" in result
    assert "# Resident Background" in result
    assert "# Current Context" in result
    assert "# Possible Actions" in result
    assert "# Required JSON Response Format" in result
    assert '"selected_action": "<one of possible_actions>"' in result
    assert "Elliot is in the bedroom." in result
    assert "Bedroom motion detected" in result
    assert "turn_light_on" in result


def test_build_decision_prompt_handles_empty_rules_and_actions_lists():
    house_state = HouseState(current_time=datetime(2026, 5, 21, 9, 0, tzinfo=timezone.utc))

    result = build_decision_prompt(house_state=house_state, possible_actions=[], house_rules=[])

    assert "# House Rules" in result
    assert "- (none)" in result
