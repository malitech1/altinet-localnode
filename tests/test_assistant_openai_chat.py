from fastapi.testclient import TestClient

from altinet.assistant.openai_engine import chat_with_ahlan
from altinet.assistant.prompt_builder import build_ahlan_prompt
from altinet.display.app import create_app
from altinet.users.models import UserPreference, UserProfile, UserRoutine


class _MockResponse:
    output_text = 'Hello from OpenAI'


class _MockClient:
    class responses:
        @staticmethod
        def create(**_kwargs):
            return _MockResponse()


def test_prompt_builder_includes_user_profile_fields():
    profile = UserProfile(
        display_name="Nora Vega",
        preferred_name="Nora",
        role="resident",
        access_level="trusted_resident",
        notes="Night shift worker",
        preferences=[UserPreference(key="light_temp", value="warm")],
        routines=[UserRoutine(name="Bedtime", schedule="22:00")],
    )
    prompt = build_ahlan_prompt(profile, {"home_name": "MyHome"}, [{"role": "user", "content": "hi"}])

    assert "Nora Vega" in prompt
    assert "preferred_name" in prompt
    assert "trusted_resident" in prompt
    assert "light_temp" in prompt
    assert "Bedtime" in prompt


def test_missing_api_key_falls_back_locally(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = chat_with_ahlan("My name is Sam")
    assert result.used_openai is False
    assert result.model
    assert "Thanks Sam" in result.reply


def test_mocked_openai_response_returns_reply(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("altinet.assistant.openai_engine.OpenAI", lambda api_key: _MockClient())
    result = chat_with_ahlan("hello")
    assert result.used_openai is True
    assert result.model
    assert result.reply == "Hello from OpenAI"


def test_api_assistant_chat_returns_valid_json(monkeypatch):
    monkeypatch.setattr(
        "altinet.display.routes.chat_with_ahlan",
        lambda message, user_id, recent_messages: type(
            "Result", (), {"model_dump": lambda self: {"reply": "ok", "suggested_profile_updates": [], "used_openai": False, "model": "gpt-5.5-mini", "error": None}}
        )(),
    )
    client = TestClient(create_app())
    response = client.post("/api/assistant/chat", json={"message": "hello", "user_id": "u1"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reply"] == "ok"
    assert isinstance(payload["suggested_profile_updates"], list)
    assert isinstance(payload["used_openai"], bool)
    assert "model" in payload
    assert "error" in payload


def test_api_assistant_chat_works_without_openai_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(create_app())
    response = client.post("/api/assistant/chat", json={"message": "My name is Elliot"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["used_openai"] is False
    assert isinstance(payload["reply"], str)
    assert payload["reply"]


def test_api_assistant_status_env_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(create_app())
    response = client.get("/api/assistant/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["openai_configured"] is False
    assert payload["engine"] == "local_fallback"


def test_api_assistant_status_env_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AHLAN_MODEL", "gpt-5.5-mini")
    client = TestClient(create_app())
    response = client.get("/api/assistant/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["openai_configured"] is True
    assert payload["engine"] == "openai"


def test_openai_exception_returns_error_string(monkeypatch):
    class _RaisingClient:
        class responses:
            @staticmethod
            def create(**_kwargs):
                raise ValueError("invalid payload")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("altinet.assistant.openai_engine.OpenAI", lambda api_key: _RaisingClient())
    result = chat_with_ahlan("hello")
    assert result.used_openai is False
    assert result.error == "ValueError: invalid payload"

