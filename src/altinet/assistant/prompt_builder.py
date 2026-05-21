from __future__ import annotations

import json

from altinet.users.models import UserProfile

AHLAN_BASE_PROMPT = """You are AHLAN (Autonomous Home Language Assistant Network), the voice/interface of the Altinet LocalNode.

Your role:
- Help the resident interact with the home.
- Learn user preferences carefully over time.
- Explain clearly what the home is doing.
- Help manage rooms, lights, appliances, perception pods, routines, and safety.
- Respect privacy.
- Never claim to control real devices unless the backend confirms the action exists.
- Ask before saving any new preferences to a user profile.
- Be warm, calm, practical, and brief.

You must return strict JSON with this shape:
{
  "reply": "string",
  "suggested_profile_updates": [
    {
      "type": "preference|routine|note",
      "summary": "string",
      "confidence": 0.0
    }
  ]
}
"""


def _profile_block(user_profile: UserProfile | None) -> dict:
    if user_profile is None:
        return {"summary": "Current user is unknown."}
    return {
        "display_name": user_profile.display_name,
        "preferred_name": user_profile.preferred_name,
        "role": user_profile.role,
        "access_level": user_profile.access_level,
        "notes": user_profile.notes,
        "saved_preferences": [pref.model_dump() for pref in user_profile.preferences],
        "saved_routines": [routine.model_dump() for routine in user_profile.routines],
    }


def build_ahlan_prompt(
    user_profile: UserProfile | None,
    home_state: dict | None,
    recent_messages: list[dict] | None,
) -> str:
    context = {
        "user_profile": _profile_block(user_profile),
        "home_summary": home_state or {},
        "recent_conversation_messages": recent_messages or [],
    }
    return f"{AHLAN_BASE_PROMPT}\n\nContext:\n{json.dumps(context, indent=2)}"
