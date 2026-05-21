from __future__ import annotations

from pydantic import BaseModel, Field
from altinet.core.ids import new_id


class DeviceProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("device"))
    name: str
    device_type: str
    room_id: str | None = None
    floor_id: str | None = None
    controllable: bool = True
    state: dict[str, str | int | float | bool] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    notes: str = ""
