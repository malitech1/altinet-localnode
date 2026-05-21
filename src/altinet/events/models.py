"""Typed event models for streaming house updates."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    timestamp: datetime
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class PersonEnteredRoom(EventBase):
    person_id: str
    room_id: str
    metadata: dict[str, str] = Field(default_factory=dict)


class PersonLeftRoom(EventBase):
    person_id: str
    room_id: str
    metadata: dict[str, str] = Field(default_factory=dict)


class DeviceStateChanged(EventBase):
    device_id: str
    is_on: bool
    metadata: dict[str, str] = Field(default_factory=dict)


class MotionDetected(EventBase):
    room_id: str
    metadata: dict[str, str] = Field(default_factory=dict)


class AudioDetected(EventBase):
    room_id: str
    level: float
    metadata: dict[str, str] = Field(default_factory=dict)


class TimeTick(EventBase):
    metadata: dict[str, str] = Field(default_factory=dict)


AltinetEvent = (
    PersonEnteredRoom
    | PersonLeftRoom
    | DeviceStateChanged
    | MotionDetected
    | AudioDetected
    | TimeTick
)
