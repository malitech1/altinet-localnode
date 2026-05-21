from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class UserPreference(BaseModel):
    key: str
    value: str
    category: str | None = None


class UserRoutine(BaseModel):
    name: str
    schedule: str | None = None
    notes: str | None = None


class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    display_name: str = Field(min_length=1)
    legal_name: str | None = None
    role: Literal["resident", "guest", "child", "admin", "service_person", "unknown"] = "unknown"
    access_level: Literal["owner", "trusted_resident", "resident", "guest", "restricted", "blocked"] = "guest"
    preferred_name: str = Field(min_length=1)
    pronouns: str | None = None
    notes: str | None = None
    preferences: list[UserPreference] = Field(default_factory=list)
    routines: list[UserRoutine] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserAccessLevel(BaseModel):
    user_id: str
    level: Literal["owner", "trusted_resident", "resident", "guest", "restricted", "blocked"]
    reason: str | None = None

