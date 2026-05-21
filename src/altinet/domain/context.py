from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from altinet.core.time import utc_now_iso

PreferenceDomain = Literal["lighting", "climate", "privacy", "security", "food", "accessibility", "communication", "other"]


class UserPreference(BaseModel):
    domain: PreferenceDomain
    summary: str
    location: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    source: str = "manual"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class UserRoutine(BaseModel):
    summary: str
    days: list[str] | None = None
    time_window: str | None = None
    location: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    source: str = "manual"


class UserPermission(BaseModel):
    action: str
    allowed: bool
    conditions: str | None = None


class UserSafetyNote(BaseModel):
    summary: str
    severity: Literal["low", "medium", "high"] = "low"
    source: str = "manual"


class UserContext(BaseModel):
    summary: str
    tags: list[str] = Field(default_factory=list)
    source: str = "manual"
    created_at: str = Field(default_factory=utc_now_iso)
