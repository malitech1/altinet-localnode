import json
from pathlib import Path

from altinet.context.schemas import HouseState
from altinet.decision.mock_engine import decide_action


def _load_sample() -> HouseState:
    sample = Path("examples/sample_house_state.json")
    return HouseState.model_validate(json.loads(sample.read_text(encoding="utf-8")))


def test_decide_turns_light_on_for_elliot_at_night_with_light_off():
    house_state = _load_sample()

    decision = decide_action(house_state)

    assert decision.selected_action == "turn_light_on"
    assert "prefers" in decision.explanation
    assert decision.confidence >= 0.9


def test_decide_does_nothing_if_light_already_on():
    house_state = _load_sample()
    house_state.rooms[0].light_on = True

    decision = decide_action(house_state)

    assert decision.selected_action == "do_nothing"
    assert "already on" in decision.explanation


def test_decide_does_nothing_for_empty_room():
    house_state = _load_sample()
    house_state.rooms[0].occupied_by_resident_ids = []

    decision = decide_action(house_state)

    assert decision.selected_action == "do_nothing"
    assert "No occupied room" in decision.explanation
