from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator

from altinet.core.ids import new_id
from altinet.core.time import utc_now_iso
from altinet.domain.access import AccessCategory, AccessLevel, get_access_category
from altinet.domain.context import UserContext, UserPermission, UserPreference, UserRoutine, UserSafetyNote


class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("user"))
    display_name: str
    preferred_name: str | None = None
    legal_name: str | None = None
    access_level: AccessLevel = AccessLevel.UNKNOWN
    category: AccessCategory | None = None
    relationship_to_home: str | None = None
    status: Literal["active", "inactive", "archived"] = "active"
    notes: str = ""
    contextual_information: list[UserContext] = Field(default_factory=list)
    preferences: list[UserPreference] = Field(default_factory=list)
    routines: list[UserRoutine] = Field(default_factory=list)
    safety_notes: list[UserSafetyNote] = Field(default_factory=list)
    permissions: list[UserPermission] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)

    @model_validator(mode="after")
    def ensure_category(self) -> "UserProfile":
        if self.category is None:
            self.category = get_access_category(self.access_level)
        return self
