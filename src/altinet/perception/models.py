"""Pydantic models for local webcam perception."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class CameraFrame(BaseModel):
    """A captured camera frame and metadata."""

    image_path: Path
    captured_at: datetime
    camera_available: bool = True


class DetectedEntity(BaseModel):
    """Generic entity observed in the room."""

    name: str
    confidence: float = Field(ge=0.0, le=1.0)


class DetectedDevice(BaseModel):
    """Device-like object observed in the room."""

    name: str
    state: str = "unknown"
    confidence: float = Field(ge=0.0, le=1.0)


class LightingObservation(BaseModel):
    """Lighting estimate from image brightness."""

    brightness_estimate: float = Field(ge=0.0, le=255.0)
    lighting_guess: str = Field(pattern="^(bright|dim|dark|unknown)$")


class RoomObservation(BaseModel):
    """Structured room-level observation."""

    image_path: Path
    timestamp: datetime
    camera_available: bool
    lighting: LightingObservation
    detected_entities: list[DetectedEntity] = Field(default_factory=list)
    detected_devices: list[DetectedDevice] = Field(default_factory=list)


class PerceptionObservation(BaseModel):
    """Top-level result for local perception pipeline."""

    source: str = "webcam"
    frame: CameraFrame
    room: RoomObservation
