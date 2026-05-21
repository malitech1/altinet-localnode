from __future__ import annotations

import json
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


class SuggestedProfileUpdate(BaseModel):
    type: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)


class AhlanChatResult(BaseModel):
    reply: str
    suggested_profile_updates: list[SuggestedProfileUpdate] = Field(default_factory=list)
    used_openai: bool
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


def chat_with_ahlan(message: str, user_id: str | None = None, recent_messages: list[dict] | None = None) -> AhlanChatResult:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("AHLAN_MODEL", "gpt-5.5-mini")
    if not api_key:
        fallback = generate_local_response(message)
        return AhlanChatResult(reply=fallback.message.content, used_openai=False)

    try:
        profile = _resolve_user(user_id)
        prompt = build_ahlan_prompt(profile, _home_summary(), recent_messages)
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message},
            ],
        )
        payload = json.loads(response.output_text)
        parsed = AhlanChatResult(
            reply=payload.get("reply", "I can help with that."),
            suggested_profile_updates=payload.get("suggested_profile_updates", []),
            used_openai=True,
            error=None,
        )
        return parsed
    except Exception as exc:
        fallback = generate_local_response(message)
        return AhlanChatResult(
            reply=fallback.message.content,
            suggested_profile_updates=[],
            used_openai=False,
            error=f"OpenAI unavailable right now ({exc.__class__.__name__}). Using local fallback.",
        )
