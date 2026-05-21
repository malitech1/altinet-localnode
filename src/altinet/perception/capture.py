"""Camera capture utilities for local perception tests."""

from __future__ import annotations

from pathlib import Path

from altinet.perception.webcam import DEFAULT_CAPTURE_PATH, capture_single_frame


def capture_room_image(output_path: Path = DEFAULT_CAPTURE_PATH, *, show_preview: bool = True) -> tuple[bool, str]:
    """Capture a single frame from the default webcam and save it.

    Returns:
        tuple[bool, str]: (success flag, human-readable status message)
    """

    success, message, _saved_path, _captured_at = capture_single_frame(output_path)
    # show_preview kept for backward compatibility; preview intentionally omitted for cross-platform simplicity.
    _ = show_preview
    return success, message
