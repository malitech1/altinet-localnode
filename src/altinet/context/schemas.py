"""Core typed schemas for Altinet LocalNode context and decisions."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Resident(BaseModel):
    id: str
    name: str
    current_room_id: str | None = None
    preferences: dict[str, str] = Field(default_factory=dict)


class Pet(BaseModel):
    id: str
    name: str
    species: str
    current_room_id: str | None = None


class Room(BaseModel):
    id: str
    name: str
    occupied_by_resident_ids: list[str] = Field(default_factory=list)
    occupied_by_pet_ids: list[str] = Field(default_factory=list)
    light_on: bool = False


class Device(BaseModel):
    id: str
    room_id: str
    device_type: str
    is_on: bool = False


class SensorReading(BaseModel):
    sensor_id: str
    room_id: str
    metric: str
    value: float
    unit: str
    recorded_at: datetime


class HouseState(BaseModel):
    residents: list[Resident] = Field(default_factory=list)
    pets: list[Pet] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    devices: list[Device] = Field(default_factory=list)
    sensor_readings: list[SensorReading] = Field(default_factory=list)
    current_time: datetime
    user_preferences: dict[str, str] = Field(default_factory=dict)


class PossibleAction(StrEnum):
    TURN_LIGHT_ON = "turn_light_on"
    TURN_LIGHT_OFF = "turn_light_off"
    DO_NOTHING = "do_nothing"


class DecisionRequest(BaseModel):
    house_state: HouseState
    possible_actions: list[PossibleAction] = Field(default_factory=list)


class DecisionResponse(BaseModel):
    selected_action: PossibleAction
    rationale: str
