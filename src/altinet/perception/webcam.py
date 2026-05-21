"""Webcam utilities for local room perception."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CAPTURE_PATH = Path("data/captures/latest.jpg")


def open_default_webcam():
    """Return an OpenCV VideoCapture for the default camera."""

    try:
        import cv2
    except ModuleNotFoundError:
        return None

    return cv2.VideoCapture(0)


def capture_single_frame(
    output_path: Path = DEFAULT_CAPTURE_PATH,
    *,
    save_timestamped: bool = False,
) -> tuple[bool, str, Path | None, datetime]:
    """Capture one frame and save it to disk.

    Returns (success, message, saved_path, timestamp).
    """

    try:
        import cv2
    except ModuleNotFoundError:
        captured_at = datetime.now(timezone.utc)
        return False, "OpenCV is not installed; webcam capture unavailable.", None, captured_at

    captured_at = datetime.now(timezone.utc)
    camera = open_default_webcam()
    if camera is None or not camera.isOpened():
        return False, "No camera detected or camera is unavailable.", None, captured_at

    try:
        ok, frame = camera.read()
        if not ok or frame is None:
            return False, "Could not read a frame from the camera.", None, captured_at

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), frame)

        if save_timestamped:
            stamp = captured_at.strftime("%Y%m%d_%H%M%S")
            timestamped_path = output_path.parent / f"capture_{stamp}.jpg"
            cv2.imwrite(str(timestamped_path), frame)

        return True, f"Captured image saved to {output_path}", output_path, captured_at
    finally:
        camera.release()
