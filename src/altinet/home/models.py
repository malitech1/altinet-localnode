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


class RoomRegion(BaseModel):
    id: str
    floor_id: str
    name: str
    room_type: Literal["bedroom", "kitchen", "bathroom", "living_room", "office", "laundry", "hallway", "other"] | None = None
    points: list[list[float]] = Field(default_factory=list)


class Wall(BaseModel):
    id: str
    room_id: str | None = None
    floor_id: str | None = None
    x1: float
    y1: float
    x2: float
    y2: float
    thickness: float = Field(default=0.15, gt=0)
    wall_type: Literal["external", "internal"] = "internal"
    thickness_mm: float | None = Field(default=None, gt=0)
    material: str | None = None


class Door(BaseModel):
    id: str
    room_id: str | None = None
    wall_id: str | None = None
    floor_id: str | None = None
    x: float
    y: float
    width: float = Field(gt=0)
    swing_degrees: float = 90
    position_along_wall_m: float | None = None
    width_m: float = Field(default=0.9, gt=0)
    swing_direction: str | None = None
    door_type: str | None = None


class Window(BaseModel):
    id: str
    room_id: str | None = None
    wall_id: str
    floor_id: str | None = None
    x: float
    y: float
    width: float = Field(gt=0)
    position_along_wall_m: float
    width_m: float = Field(default=1.2, gt=0)
    height_m: float | None = None
    sill_height_m: float | None = None


class Light(BaseModel):
    id: str
    room_id: str | None = None
    floor_id: str | None = None
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


class PerceptionPodPlacement(BaseModel):
    id: str
    name: str
    floor_id: str
    x: float
    y: float
    orientation_degrees: float = 0
    camera_enabled: bool = True
    microphone_enabled: bool = True
    sensors: list[str] = Field(default_factory=list)




class HomeLocation(BaseModel):
    address_line_1: str | None = None
    address_line_2: str | None = None
    suburb_city: str | None = None
    state_region: str | None = None
    postcode: str | None = None
    country: str | None = None
    formatted_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None
    address_verified: bool = False
    address_verification_source: str | None = None
    address_verified_at: str | None = None

class HomeModel(BaseModel):
    property_name: str
    address: str | None = None
    location: HomeLocation = Field(default_factory=HomeLocation)
    property_boundary: PropertyBoundary
    house_dimensions: HouseDimensions
    floors: list[Floor] = Field(default_factory=list)
    rooms: list[Room] = Field(default_factory=list)
    room_regions: list[RoomRegion] = Field(default_factory=list)
    walls: list[Wall] = Field(default_factory=list)
    doors: list[Door] = Field(default_factory=list)
    windows: list[Window] = Field(default_factory=list)
    lights: list[Light] = Field(default_factory=list)
    perception_pods: list[PerceptionPodPlacement] = Field(default_factory=list)
    device_placements: list[DevicePlacement] = Field(default_factory=list)
    units: str = "metres"
