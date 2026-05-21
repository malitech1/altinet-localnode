"""Camera capture utilities for local perception tests."""

from __future__ import annotations

from pathlib import Path


DEFAULT_CAPTURE_PATH = Path("data/captures/latest.jpg")


def capture_room_image(output_path: Path = DEFAULT_CAPTURE_PATH, *, show_preview: bool = True) -> tuple[bool, str]:
    """Capture a single frame from the default webcam and save it.

    Returns:
        tuple[bool, str]: (success flag, human-readable status message)
    """

    import cv2

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        return False, "No camera detected or camera is unavailable."

    try:
        ok, frame = camera.read()
        if not ok or frame is None:
            return False, "Could not read a frame from the camera."

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), frame)

        if show_preview:
            try:
                cv2.imshow("Altinet Capture Preview", frame)
                cv2.waitKey(1200)
                cv2.destroyAllWindows()
            except cv2.error:
                # Headless/GUI-limited environments should not fail capture.
                pass

        return True, f"Captured image saved to {output_path}"
    finally:
        camera.release()
