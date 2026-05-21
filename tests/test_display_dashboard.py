from fastapi.testclient import TestClient

from altinet.display.routes import CAPTURE_PATH, ROOM_CONTEXT_PATH, RUNTIME_STATE_PATH
from altinet.display.app import create_app


def test_fastapi_app_starts():
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "Altinet LocalNode" in response.text


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
    assert payload["runtime_state"] is None
    assert payload["room_context"] is None
    assert payload["capture_available"] is False

    capture_response = client.get("/captures/latest.jpg")
    assert capture_response.status_code == 404
    assert "No captured image" in capture_response.text
