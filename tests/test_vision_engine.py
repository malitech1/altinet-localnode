import json
import sys
import types

import pytest

from altinet.perception.vision_engine import analyse_room_image_with_openai


class _FakeResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _FakeClient:
    def __init__(self, output_text: str):
        self.responses = self
        self._output_text = output_text

    def create(self, **_kwargs):
        return _FakeResponse(self._output_text)


def _install_fake_openai(monkeypatch, output_text: str) -> None:
    fake_mod = types.SimpleNamespace(OpenAI=lambda api_key: _FakeClient(output_text))
    monkeypatch.setitem(sys.modules, "openai", fake_mod)


def test_analyse_room_image_with_openai_validates_schema(monkeypatch, tmp_path):
    image_path = tmp_path / "latest.jpg"
    image_path.write_bytes(b"fake")

    payload = {
        "room_type_guess": "office",
        "visible_people": ["adult"],
        "visible_pets": [],
        "visible_devices": ["laptop"],
        "lights_on": True,
        "lighting_description": "ceiling light is on",
        "notable_objects": ["desk"],
        "safety_concerns": [],
        "summary": "Small office with one workstation.",
    }

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_VISION_MODEL", "gpt-test-vision")
    _install_fake_openai(monkeypatch, json.dumps(payload))

    result = analyse_room_image_with_openai(image_path)

    assert result.room_type_guess == "office"
    assert result.visible_devices == ["laptop"]
    assert result.lighting_description == "ceiling light is on"


def test_analyse_room_image_with_openai_handles_missing_api_key(monkeypatch, tmp_path):
    image_path = tmp_path / "latest.jpg"
    image_path.write_bytes(b"fake")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc:
        analyse_room_image_with_openai(image_path)

    assert "OPENAI_API_KEY is not set" in str(exc.value)
    assert "observe-room" in str(exc.value)


def test_analyse_room_image_with_openai_rejects_invalid_json(monkeypatch, tmp_path):
    image_path = tmp_path / "latest.jpg"
    image_path.write_bytes(b"fake")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    _install_fake_openai(monkeypatch, '{"room_type_guess":"garage"}')

    with pytest.raises(RuntimeError) as exc:
        analyse_room_image_with_openai(image_path)

    assert "does not match RoomContextResponse" in str(exc.value)
