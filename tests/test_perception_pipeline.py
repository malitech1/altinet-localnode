from datetime import datetime, timezone
from pathlib import Path

import pytest

from altinet.perception.models import LightingObservation, PerceptionObservation
from altinet.perception.pipeline import classify_lighting, estimate_brightness_from_image, observe_room


def test_model_validation_rejects_invalid_lighting_guess():
    with pytest.raises(Exception):
        LightingObservation(brightness_estimate=100, lighting_guess="sunny")


def test_brightness_classification():
    assert classify_lighting(20) == "dark"
    assert classify_lighting(80) == "dim"
    assert classify_lighting(200) == "bright"


def test_missing_image_handling_returns_none(tmp_path):
    missing_image = tmp_path / "missing.jpg"
    assert estimate_brightness_from_image(missing_image) is None


def test_pipeline_output_structure(monkeypatch, tmp_path):
    image_path = tmp_path / "latest.jpg"
    image_path.write_bytes(b"fake")

    def _fake_capture(_capture_path):
        return True, "ok", image_path, datetime.now(timezone.utc)

    monkeypatch.setattr("altinet.perception.pipeline.capture_single_frame", _fake_capture)
    monkeypatch.setattr("altinet.perception.pipeline.estimate_brightness_from_image", lambda _path: 150.0)

    result = observe_room(capture_path=tmp_path / "unused.jpg")

    assert isinstance(result, PerceptionObservation)
    assert result.frame.camera_available is True
    assert result.room.lighting.lighting_guess == "bright"
    assert result.room.image_path == image_path


def test_pipeline_handles_missing_webcam(monkeypatch, tmp_path):
    def _fake_capture(_capture_path):
        return False, "no camera", None, datetime.now(timezone.utc)

    monkeypatch.setattr("altinet.perception.pipeline.capture_single_frame", _fake_capture)

    result = observe_room(capture_path=tmp_path / "latest.jpg")

    assert result.frame.camera_available is False
    assert result.room.lighting.lighting_guess == "unknown"
