from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PropertyBoundary(BaseModel):
    width: float = Field(gt=0)
    depth: float = Field(gt=0)


class HouseDimensions(BaseModel):
    width: float = Field(gt=0)
    depth: float = Field(gt=0)


class Floor(BaseModel):
    id: str
    name: str
    level: int = 0


class Room(BaseModel):
    id: str
    floor_id: str
    name: str
    x: float = 0
    y: float = 0
    width: float = Field(gt=0)
    depth: float = Field(gt=0)


class Wall(BaseModel):
    id: str
    room_id: str
    x1: float
    y1: float
    x2: float
    y2: float
    thickness: float = Field(default=0.15, gt=0)


class Door(BaseModel):
    id: str
    room_id: str
    wall_id: str
    x: float
    y: float
    width: float = Field(gt=0)
    swing_degrees: float = 90


class Window(BaseModel):
    id: str
    room_id: str
    wall_id: str
    x: float
    y: float
    width: float = Field(gt=0)


class Light(BaseModel):
    id: str
    room_id: str
    name: str
    x: float
    y: float
    type: Literal["ceiling", "wall", "lamp"] = "ceiling"


class DevicePlacement(BaseModel):
    id: str
    device_id: str
    room_id: str
    x: float
    y: float
    kind: str = "light"


class HomeModel(BaseModel):
    property_name: str
    address: str | None = None
    property_boundary: PropertyBoundary
    house_dimensions: HouseDimensions
    floors: list[Floor] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    walls: list[Wall] = Field(default_factory=list)
    doors: list[Door] = Field(default_factory=list)
    windows: list[Window] = Field(default_factory=list)
    lights: list[Light] = Field(default_factory=list)
    device_placements: list[DevicePlacement] = Field(default_factory=list)
    units: str = "metres"
