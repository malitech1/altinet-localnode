from fastapi.testclient import TestClient

from altinet.display.routes import CAPTURE_PATH, ROOM_CONTEXT_PATH, RUNTIME_STATE_PATH
from altinet.display.app import create_app


def test_fastapi_app_starts():
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "Altinet LocalNode" in response.text


def test_dashboard_renders_template_successfully():
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>Altinet LocalNode Dashboard</title>" in response.text


def test_api_state_returns_json():
    client = TestClient(create_app())
    response = client.get("/api/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Altinet LocalNode"
    assert "current_time" in payload


def test_missing_files_handled_gracefully(monkeypatch, tmp_path):
    monkeypatch.setattr("altinet.display.routes.RUNTIME_STATE_PATH", tmp_path / "missing_runtime_state.json")
    monkeypatch.setattr("altinet.display.routes.ROOM_CONTEXT_PATH", tmp_path / "missing_room_context.json")
    monkeypatch.setattr("altinet.display.routes.CAPTURE_PATH", tmp_path / "missing.jpg")

    client = TestClient(create_app())
    response = client.get("/api/state")

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_state"] == {}
    assert payload["room_context"] == {}
    assert payload["system_status"] == "All systems operational"
    assert isinstance(payload["residents"], list)
    assert isinstance(payload["decisions"], list)
    assert isinstance(payload["home_summary"], dict)
    assert isinstance(payload["weather"], dict)
    assert isinstance(payload["perception"], str)
    assert payload["capture_available"] is False

    capture_response = client.get("/captures/latest.jpg")
    assert capture_response.status_code == 404
    assert "No captured image" in capture_response.text


def test_dashboard_does_not_crash_when_optional_data_files_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("altinet.display.routes.RUNTIME_STATE_PATH", tmp_path / "missing_runtime_state.json")
    monkeypatch.setattr("altinet.display.routes.ROOM_CONTEXT_PATH", tmp_path / "missing_room_context.json")
    monkeypatch.setattr("altinet.display.routes.CAPTURE_PATH", tmp_path / "missing.jpg")

    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "Altinet LocalNode" in response.text


def test_dashboard_contains_home_builder_navigation_links():
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert '/home-builder' in response.text
    assert 'Edit Home / Floorplan' in response.text


def test_dashboard_contains_required_element_ids():
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    for element_id in [
        "header-date",
        "current-time",
        "system-status",
        "residents-list",
        "floorplan-grid",
        "decisions-list",
        "assistant-chat",
        "assistant-mode",
        "assistant-send",
        "assistant-input",
    ]:
        assert f'id="{element_id}"' in response.text
