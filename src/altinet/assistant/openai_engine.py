from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from altinet.assistant.local_engine import generate_local_response
from altinet.assistant.prompt_builder import build_ahlan_prompt
from altinet.home.storage import load_home_model
from altinet.users.models import UserProfile
from altinet.users.storage import load_user_profiles

load_dotenv()
logger = logging.getLogger(__name__)
DEFAULT_AHLAN_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")


class SuggestedProfileUpdate(BaseModel):
    type: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class AhlanChatResult(BaseModel):
    reply: str
    suggested_profile_updates: list[SuggestedProfileUpdate] = Field(default_factory=list)
    used_openai: bool
    model: str
    error: str | None = None


def _resolve_user(user_id: str | None) -> UserProfile | None:
    if not user_id:
        return None
    return next((p for p in load_user_profiles() if p.id == user_id), None)


def _home_summary() -> dict:
    home = load_home_model()
    return {
        "property_name": home.property_name,
        "rooms": [room.name for room in home.rooms],
        "lights": [light.name for light in home.lights],
        "appliances": [device.device_id for device in home.device_placements],
        "perception_pods": [pod.name for pod in home.perception_pods],
    }


def _resolve_model() -> str:
    model = (os.getenv("AHLAN_MODEL") or "").strip()
    return model or DEFAULT_AHLAN_MODEL


def _extract_output_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") in {"output_text", "text"}:
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        chunks.append(text.strip())
        if chunks:
            return "\n".join(chunks)

    return "I can help with that."


def chat_with_ahlan(message: str, user_id: str | None = None, recent_messages: list[dict] | None = None) -> AhlanChatResult:
    api_key = os.getenv("OPENAI_API_KEY")
    model = _resolve_model()
    if not api_key:
        fallback = generate_local_response(message)
        return AhlanChatResult(reply=fallback.message.content, used_openai=False, model=model)

    try:
        profile = _resolve_user(user_id)
        system_prompt = build_ahlan_prompt(profile, _home_summary(), recent_messages)
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )

        return AhlanChatResult(
            reply=_extract_output_text(response),
            suggested_profile_updates=[],
            used_openai=True,
            model=model,
            error=None,
        )
    except Exception as exc:
        logger.exception("AHLAN OpenAI request failed")
        fallback = generate_local_response(message)
        short_message = str(exc).splitlines()[0]
        error_label = f"{exc.__class__.__name__}: {short_message}"
        return AhlanChatResult(
            reply=fallback.message.content,
            suggested_profile_updates=[],
            used_openai=False,
            model=model,
            error=error_label,
        )
