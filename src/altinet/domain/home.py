from __future__ import annotations

from pydantic import BaseModel, Field
from altinet.core.ids import new_id
from altinet.core.time import utc_now_iso


class ZoneProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("zone"))
    name: str
    type: str = "generic"
    dimensions: dict[str, float] = Field(default_factory=dict)
    floor_id: str | None = None
    notes: str = ""
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class RoomProfile(ZoneProfile):
    id: str = Field(default_factory=lambda: new_id("room"))


class FloorProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("floor"))
    name: str
    type: str = "floor"
    dimensions: dict[str, float] = Field(default_factory=dict)
    floor_id: str | None = None
    notes: str = ""
    rooms: list[RoomProfile] = Field(default_factory=list)
    zones: list[ZoneProfile] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class HomeProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("home"))
    name: str = "Altinet Home"
    type: str = "residential"
    dimensions: dict[str, float] = Field(default_factory=dict)
    floor_id: str | None = None
    notes: str = ""
    floors: list[FloorProfile] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
