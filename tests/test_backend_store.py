from pathlib import Path

from fastapi.testclient import TestClient

from altinet.display.app import create_app
from altinet.domain.access import AccessCategory, AccessLevel, get_access_category
from altinet.domain.context import UserPreference, UserRoutine
from altinet.domain.users import UserProfile
from altinet.main import _seed_demo_data
from altinet.store.registry import RegistryService
from altinet.store.repositories.users_repository import UsersRepository


def test_access_levels_values():
    assert AccessLevel.RESIDENT_OWNER.value == "resident_owner"
    assert AccessLevel.INTRUDER.value == "intruder"


def test_access_category_mapping():
    assert get_access_category(AccessLevel.GUEST_FAMILY) == AccessCategory.GUEST
    assert get_access_category(AccessLevel.BLOCKED) == AccessCategory.THREAT


def test_user_profile_validation_derives_category():
    user = UserProfile(display_name="X", access_level=AccessLevel.CHILD)
    assert user.category == AccessCategory.DEPENDENT


def test_users_repository_crud(tmp_path: Path):
    repo = UsersRepository(tmp_path / "users.json")
    created = repo.create_user(UserProfile(display_name="Elliot", access_level=AccessLevel.RESIDENT_OWNER))
    assert repo.get_user(created.id) is not None
    assert len(repo.list_users()) == 1
    updated = repo.update_user(created.id, {"status": "inactive"})
    assert updated is not None and updated.status == "inactive"
    assert repo.delete_user(created.id) is True
    assert repo.get_user(created.id) is None


def test_add_preference_and_routine(tmp_path: Path):
    repo = UsersRepository(tmp_path / "users.json")
    created = repo.create_user(UserProfile(display_name="A"))
    updated = repo.add_preference(created.id, UserPreference(domain="lighting", summary="dim at night"))
    assert updated is not None and len(updated.preferences) == 1
    updated = repo.add_routine(created.id, UserRoutine(summary="morning walk"))
    assert updated is not None and len(updated.routines) == 1


def test_registry_load_save(tmp_path: Path):
    reg = RegistryService(tmp_path)
    reg.users.create_user(UserProfile(display_name="X"))
    state = reg.load_registry()
    assert len(state["users"]) == 1


def test_seed_demo_data_creates_expected_records():
    _seed_demo_data()
    state = RegistryService().load_registry()
    names = {u["display_name"] for u in state["users"]}
    assert "Elliot" in names
    assert any(a["name"] == "AHLAN" for a in state["agents"]["agents"])


def test_api_users_endpoints(tmp_path: Path, monkeypatch):
    from altinet.store import repositories
    from altinet.store.repositories import users_repository
    users_repository._repo = UsersRepository(tmp_path / "users.json")

    app = create_app()
    client = TestClient(app)

    resp = client.post("/api/users", json={"display_name": "Api User"})
    assert resp.status_code == 200
    user_id = resp.json()["id"]

    assert client.get("/api/users").status_code == 200
    assert client.get(f"/api/users/{user_id}").status_code == 200
    assert client.patch(f"/api/users/{user_id}", json={"status": "inactive"}).status_code == 200
    assert client.post(f"/api/users/{user_id}/preferences", json={"domain": "lighting", "summary": "warm"}).status_code == 200
    assert client.post(f"/api/users/{user_id}/routines", json={"summary": "8am breakfast"}).status_code == 200
    assert client.post(f"/api/users/{user_id}/context-notes", json={"summary": "works from home"}).status_code == 200
    assert client.delete(f"/api/users/{user_id}").status_code == 200
