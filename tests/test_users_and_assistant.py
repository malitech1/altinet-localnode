from fastapi.testclient import TestClient
from pydantic import ValidationError

from altinet.assistant.local_engine import generate_local_response
from altinet.display.app import create_app
from altinet.store.repositories.users_repository import UsersRepository
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
    monkeypatch.setattr("altinet.store.repositories.users_repository._repo", UsersRepository(users_path))

    client = TestClient(create_app())
    create_response = client.post("/api/users", json={"display_name": "Nora", "preferred_name": "Nora", "access_level": "resident_standard"})
    assert create_response.status_code == 200

    response = client.get("/api/users")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["display_name"] == "Nora"


def test_api_users_returns_empty_array_when_missing_file(monkeypatch, tmp_path):
    users_path = tmp_path / "missing_users.json"
    monkeypatch.setattr("altinet.store.repositories.users_repository._repo", UsersRepository(users_path))
    client = TestClient(create_app())
    response = client.get("/api/users")
    assert response.status_code == 200
    assert response.json() == []


def test_local_assistant_engine_returns_response():
    response = generate_local_response("My name is Elliot")
    assert "Thanks Elliot" in response.message.content


def test_post_seed_demo_creates_demo_users(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr("altinet.store.repositories.users_repository._repo", UsersRepository(users_path))
    client = TestClient(create_app())
    response = client.post("/api/registry/seed-demo")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert len(body["users"]) >= 1


def test_api_state_includes_users(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr("altinet.store.repositories.users_repository._repo", UsersRepository(users_path))
    client = TestClient(create_app())
    client.post("/api/users", json={"display_name": "State User", "access_level": "resident_standard"})
    response = client.get("/api/state")
    assert response.status_code == 200
    payload = response.json()
    assert "users" in payload
    assert "residents" in payload
    assert "system_status" in payload
    assert payload["registry_available"] is True


def test_post_users_creates_backend_user(monkeypatch, tmp_path):
    users_path = tmp_path / "users.json"
    monkeypatch.setattr("altinet.store.repositories.users_repository._repo", UsersRepository(users_path))
    client = TestClient(create_app())
    response = client.post("/api/users", json={"display_name": "Casey", "access_level": "guest_visitor", "notes": "temporary"})
    assert response.status_code == 200
    stored = UsersRepository(users_path).list_users()
    assert any(u.display_name == "Casey" for u in stored)
