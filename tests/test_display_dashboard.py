from pathlib import Path
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


def test_settings_route_returns_200_and_has_home_location_section():
    client = TestClient(create_app())
    response = client.get('/settings')
    assert response.status_code == 200
    assert 'Home Location' in response.text
    assert '/api/home/location' in Path('src/altinet/display/static/settings.js').read_text(encoding='utf-8')
    assert '/api/home/location/verify' in Path('src/altinet/display/static/settings.js').read_text(encoding='utf-8')


def test_dashboard_links_to_settings_and_no_home_location_form():
    client = TestClient(create_app())
    response = client.get('/')
    assert '/settings' in response.text
    assert 'id="home-location-form"' not in response.text


def test_dashboard_contains_required_element_ids():
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    for element_id in [
        "dashboard-status",
        "users-list",
        "add-user-button",
        "add-user-form",
        "user-display-name",
        "user-preferred-name",
        "user-access-level",
        "user-contextual-information",
        "save-user-button",
        "cancel-user-button",
    ]:
        assert f'id="{element_id}"' in response.text


def test_dashboard_contains_user_list_and_seed_button():
    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert "id=\"users-list\"" in response.text
    assert "id=\"seed-demo-users-button\"" in response.text


def test_dashboard_js_references_seed_demo_users_button():
    js = Path("src/altinet/display/static/dashboard.js").read_text(encoding="utf-8")
    assert "seed-demo-users-button" in js


def test_dashboard_js_contains_add_and_save_button_listeners():
    js = Path("src/altinet/display/static/dashboard.js").read_text(encoding="utf-8")
    assert "add-user-button" in js
    assert "save-user-button" in js


def test_dashboard_template_references_dashboard_js():
    template = Path("src/altinet/display/templates/dashboard.html").read_text(encoding="utf-8")
    assert '/static/dashboard.js' in template


def test_dashboard_js_file_exists():
    assert Path("src/altinet/display/static/dashboard.js").exists()


def test_dashboard_js_contains_startup_guardrails():
    js = Path("src/altinet/display/static/dashboard.js").read_text(encoding="utf-8")
    assert "Altinet dashboard.js loaded" in js
    assert "add-user-button" in js
    assert "seed-demo-users-button" in js
