from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from altinet.users.models import UserProfile

USER_PROFILES_PATH = Path(__file__).resolve().parents[3] / "data" / "users" / "user_profiles.json"


def load_user_profiles(path: Path | None = None) -> list[UserProfile]:
    path = path or USER_PROFILES_PATH
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [UserProfile.model_validate(item) for item in payload]


def save_user_profiles(profiles: list[UserProfile], path: Path | None = None) -> list[UserProfile]:
    path = path or USER_PROFILES_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([profile.model_dump(mode="json") for profile in profiles], indent=2), encoding="utf-8")
    return profiles


def create_user_profile(profile: UserProfile, path: Path | None = None) -> UserProfile:
    profiles = load_user_profiles(path)
    profiles.append(profile)
    save_user_profiles(profiles, path)
    return profile


def update_user_profile(user_id: str, updates: dict, path: Path | None = None) -> UserProfile | None:
    profiles = load_user_profiles(path)
    for index, profile in enumerate(profiles):
        if profile.id == user_id:
            merged = profile.model_dump()
            merged.update(updates)
            merged["updated_at"] = datetime.now(timezone.utc)
            updated = UserProfile.model_validate(merged)
            profiles[index] = updated
            save_user_profiles(profiles, path)
            return updated
    return None


def delete_user_profile(user_id: str, path: Path | None = None) -> bool:
    profiles = load_user_profiles(path)
    filtered = [profile for profile in profiles if profile.id != user_id]
    if len(filtered) == len(profiles):
        return False
    save_user_profiles(filtered, path)
    return True
