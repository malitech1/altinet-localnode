from __future__ import annotations

from pathlib import Path

from altinet.core.time import utc_now_iso
from altinet.domain.context import UserContext, UserPreference, UserRoutine
from altinet.domain.users import UserProfile
from altinet.store.json_store import JsonStore

DATA_FILE = Path("data/altinet/users/users.json")


class UsersRepository:
    def __init__(self, data_file: Path = DATA_FILE):
        self.store = JsonStore(data_file)

    def _load_users(self) -> list[UserProfile]:
        payload = self.store.load(default={"users": []})
        return [UserProfile.model_validate(item) for item in payload.get("users", [])]

    def _save_users(self, users: list[UserProfile]) -> None:
        self.store.save({"users": [u.model_dump(mode="json") for u in users]})

    def list_users(self) -> list[UserProfile]:
        return self._load_users()

    def get_user(self, user_id: str) -> UserProfile | None:
        return next((u for u in self._load_users() if u.id == user_id), None)

    def create_user(self, profile: UserProfile) -> UserProfile:
        users = self._load_users()
        users.append(profile)
        self._save_users(users)
        return profile

    def update_user(self, user_id: str, patch: dict) -> UserProfile | None:
        users = self._load_users()
        for i, user in enumerate(users):
            if user.id == user_id:
                merged = user.model_dump(mode="json")
                merged.update(patch)
                merged["updated_at"] = utc_now_iso()
                users[i] = UserProfile.model_validate(merged)
                self._save_users(users)
                return users[i]
        return None

    def delete_user(self, user_id: str) -> bool:
        users = self._load_users()
        filtered = [u for u in users if u.id != user_id]
        if len(filtered) == len(users):
            return False
        self._save_users(filtered)
        return True

    def add_preference(self, user_id: str, preference: UserPreference) -> UserProfile | None:
        user = self.get_user(user_id)
        if user is None:
            return None
        user.preferences.append(preference)
        return self.update_user(user_id, {"preferences": [p.model_dump(mode="json") for p in user.preferences]})

    def add_routine(self, user_id: str, routine: UserRoutine) -> UserProfile | None:
        user = self.get_user(user_id)
        if user is None:
            return None
        user.routines.append(routine)
        return self.update_user(user_id, {"routines": [r.model_dump(mode="json") for r in user.routines]})

    def add_context_note(self, user_id: str, note: UserContext) -> UserProfile | None:
        user = self.get_user(user_id)
        if user is None:
            return None
        user.contextual_information.append(note)
        return self.update_user(user_id, {"contextual_information": [c.model_dump(mode="json") for c in user.contextual_information]})


_repo = UsersRepository()


def list_users() -> list[UserProfile]:
    return _repo.list_users()


def get_user(user_id: str) -> UserProfile | None:
    return _repo.get_user(user_id)


def create_user(profile: UserProfile) -> UserProfile:
    return _repo.create_user(profile)


def update_user(user_id: str, patch: dict) -> UserProfile | None:
    return _repo.update_user(user_id, patch)


def delete_user(user_id: str) -> bool:
    return _repo.delete_user(user_id)


def add_preference(user_id: str, preference: UserPreference) -> UserProfile | None:
    return _repo.add_preference(user_id, preference)


def add_routine(user_id: str, routine: UserRoutine) -> UserProfile | None:
    return _repo.add_routine(user_id, routine)


def add_context_note(user_id: str, note: UserContext) -> UserProfile | None:
    return _repo.add_context_note(user_id, note)
