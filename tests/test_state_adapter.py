import json

from altinet.display.state_adapter import build_dashboard_state


def test_state_adapter_no_files_present(tmp_path):
    data = build_dashboard_state(
        tmp_path / "runtime_state.json",
        tmp_path / "latest_room_context.json",
        tmp_path / "latest_decision.json",
    )

    assert data["runtime_state"] is None
    assert data["room_context"] is None
    assert data["system_status"] == "waiting_for_runtime"
    assert len(data["residents"]) > 0


def test_state_adapter_with_runtime_state(tmp_path):
    runtime_path = tmp_path / "runtime_state.json"
    runtime_path.write_text(
        json.dumps(
            {
                "status": "running",
                "active_residents": ["resident_elliot"],
                "current_room_occupancy": {"living_room": ["resident_elliot"]},
                "devices": {"desk_light": {"is_on": True, "metadata": {"brightness": "30%"}}},
            }
        ),
        encoding="utf-8",
    )

    data = build_dashboard_state(runtime_path, tmp_path / "ctx.json", tmp_path / "decision.json")

    assert data["system_status"] == "running"
    assert data["residents"][0]["name"] == "Elliot"
    assert data["devices"][0]["state"] == "on"


def test_state_adapter_with_room_context(tmp_path):
    context_path = tmp_path / "latest_room_context.json"
    context_path.write_text(json.dumps({"occupants": ["Emma"], "pets": [{"name": "Nori"}]}), encoding="utf-8")

    data = build_dashboard_state(tmp_path / "runtime_state.json", context_path, tmp_path / "decision.json")

    assert data["residents"][0]["name"] == "Emma"
    assert data["pets"][0]["name"] == "Nori"


def test_state_adapter_with_latest_decision(tmp_path):
    decision_path = tmp_path / "latest_decision.json"
    decision_path.write_text(
        json.dumps({"action": "Started Washer", "rationale": "Off-peak rate", "impact": "Low Energy Use"}),
        encoding="utf-8",
    )

    data = build_dashboard_state(tmp_path / "runtime_state.json", tmp_path / "context.json", decision_path)

    assert data["decisions"][0]["action"] == "Started Washer"
    assert data["decisions"][0]["impact"] == "Low Energy Use"


def test_state_adapter_handles_malformed_file_safely(tmp_path):
    runtime_path = tmp_path / "runtime_state.json"
    runtime_path.write_text("{not valid json", encoding="utf-8")

    data = build_dashboard_state(runtime_path, tmp_path / "context.json", tmp_path / "decision.json")

    assert data["runtime_state"] is None
    assert data["system_status"] == "waiting_for_runtime"
