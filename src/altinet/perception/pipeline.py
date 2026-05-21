"""Simple local webcam perception pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from altinet.perception.models import CameraFrame, LightingObservation, PerceptionObservation, RoomObservation
from altinet.perception.webcam import DEFAULT_CAPTURE_PATH, capture_single_frame


def classify_lighting(brightness_estimate: float) -> str:
    """Map brightness [0..255] to a simple lighting label."""

    if brightness_estimate < 0:
        return "unknown"
    if brightness_estimate < 60:
        return "dark"
    if brightness_estimate < 140:
        return "dim"
    return "bright"


def estimate_brightness_from_image(image_path: Path) -> float | None:
    """Estimate image brightness as mean grayscale pixel intensity."""

    try:
        import cv2
    except ModuleNotFoundError:
        return None

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    return float(image.mean())


def observe_room(*, capture_path: Path = DEFAULT_CAPTURE_PATH) -> PerceptionObservation:
    """Capture a webcam frame and convert it into a local placeholder observation."""

    success, _message, saved_path, captured_at = capture_single_frame(capture_path)
    observation_time = captured_at if success else datetime.now(timezone.utc)

    if not success or saved_path is None:
        frame = CameraFrame(image_path=capture_path, captured_at=observation_time, camera_available=False)
        lighting = LightingObservation(brightness_estimate=0.0, lighting_guess="unknown")
    else:
        brightness = estimate_brightness_from_image(saved_path)
        brightness_value = 0.0 if brightness is None else brightness
        lighting = LightingObservation(
            brightness_estimate=brightness_value,
            lighting_guess="unknown" if brightness is None else classify_lighting(brightness_value),
        )
        frame = CameraFrame(image_path=saved_path, captured_at=observation_time, camera_available=True)

    room = RoomObservation(
        image_path=frame.image_path,
        timestamp=frame.captured_at,
        camera_available=frame.camera_available,
        lighting=lighting,
    )
    return PerceptionObservation(frame=frame, room=room)
