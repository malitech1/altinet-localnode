from fastapi.testclient import TestClient
from pydantic import ValidationError

from altinet.assistant.local_engine import generate_local_response
from altinet.display.app import create_app
from altinet.users.models import UserProfile
from altinet.users.storage import create_user_profile, delete_user_profile, load_user_profiles, save_user_profiles, update_user_profile


def test_user_profile_validation_rejects_empty_names():
    try:
        UserProfile(display_name="", preferred_name="")
        assert False
    except ValidationError:
        assert True


def test_save_and_load_user_profiles(tmp_path):
    path = tmp_path / "users.json"
    profile = UserProfile(display_name="Elliot", preferred_name="Elliot", role="resident", access_level="resident")
    save_user_profiles([profile], path)
    loaded = load_user_profiles(path)
    assert len(loaded) == 1
    assert loaded[0].display_name == "Elliot"


def test_create_update_delete_user_profile(tmp_path):
    path = tmp_path / "users.json"
    profile = UserProfile(display_name="Sam", preferred_name="Sam")
    create_user_profile(profile, path)

    updated = update_user_profile(profile.id, {"notes": "Night shift"}, path)
    assert updated is not None
    assert updated.notes == "Night shift"

    deleted = delete_user_profile(profile.id, path)
    assert deleted is True
    assert load_user_profiles(path) == []


def test_api_users_returns_json(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr("altinet.users.storage.USER_PROFILES_PATH", users_path)

    client = TestClient(create_app())
    create_response = client.post("/api/users", json={"display_name": "Nora", "preferred_name": "Nora", "role": "resident", "access_level": "resident"})
    assert create_response.status_code == 200

    response = client.get("/api/users")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["display_name"] == "Nora"


def test_api_users_returns_empty_array_when_missing_file(monkeypatch, tmp_path):
    users_path = tmp_path / "missing_users.json"
    monkeypatch.setattr("altinet.users.storage.USER_PROFILES_PATH", users_path)
    client = TestClient(create_app())
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.json() == []


def test_local_assistant_engine_returns_response():
    response = generate_local_response("My name is Elliot")
    assert "Thanks Elliot" in response.message.content
