from datetime import datetime, timezone

from altinet.events.models import DeviceStateChanged, PersonEnteredRoom, PersonLeftRoom
from altinet.runtime.state_manager import RuntimeStateManager


def test_runtime_state_updates_from_events_and_autosaves(tmp_path):
    state_path = tmp_path / "runtime_state.json"
    manager = RuntimeStateManager(state_path=state_path)

    t = datetime(2026, 5, 21, 20, 0, tzinfo=timezone.utc)
    manager.apply_event(
        PersonEnteredRoom(
            timestamp=t,
            source="test",
            confidence=1.0,
            person_id="resident_elliot",
            room_id="bedroom",
            metadata={},
        )
    )
    manager.apply_event(
        DeviceStateChanged(
            timestamp=t,
            source="test",
            confidence=0.9,
            device_id="bedroom_light",
            is_on=True,
            metadata={"reason": "manual"},
        )
    )

    assert manager.state.current_room_occupancy["bedroom"] == ["resident_elliot"]
    assert manager.state.devices["bedroom_light"]["is_on"] is True
    assert manager.state.active_residents == ["resident_elliot"]
    assert manager.state.timestamps["last_event"] == t
    assert state_path.exists()


def test_runtime_state_restores_from_disk_and_tracks_resident_exit(tmp_path):
    state_path = tmp_path / "runtime_state.json"
    manager = RuntimeStateManager(state_path=state_path)

    t_enter = datetime(2026, 5, 21, 20, 0, tzinfo=timezone.utc)
    t_leave = datetime(2026, 5, 21, 21, 0, tzinfo=timezone.utc)

    manager.apply_event(
        PersonEnteredRoom(
            timestamp=t_enter,
            source="test",
            confidence=1.0,
            person_id="resident_elliot",
            room_id="bedroom",
            metadata={},
        )
    )

    restored = RuntimeStateManager(state_path=state_path)
    assert restored.state.current_room_occupancy["bedroom"] == ["resident_elliot"]

    restored.apply_event(
        PersonLeftRoom(
            timestamp=t_leave,
            source="test",
            confidence=1.0,
            person_id="resident_elliot",
            room_id="bedroom",
            metadata={},
        )
    )

    assert restored.state.current_room_occupancy["bedroom"] == []
    assert restored.state.active_residents == []


def test_runtime_state_is_json_serializable(tmp_path):
    state_path = tmp_path / "runtime_state.json"
    manager = RuntimeStateManager(state_path=state_path)

    manager.set_inferred_context("quiet evening")

    serialized = manager.state.model_dump_json()
    assert '"current_inferred_context":"quiet evening"' in serialized
