"""Typed schemas for LocalNode context."""

from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str


class Room(BaseModel):
    id: str
    name: str


class SensorReading(BaseModel):
    sensor_id: str
    room_id: str
    value: float
    unit: str


class PossibleAction(BaseModel):
    action_id: str
    description: str


class HomeContext(BaseModel):
    home_id: str
    users: list[User]
    rooms: list[Room]
    sensors: list[SensorReading]
    possible_actions: list[PossibleAction]
