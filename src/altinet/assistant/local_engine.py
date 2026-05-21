from __future__ import annotations

from altinet.assistant.models import AssistantConversation, AssistantMessage, AssistantResponse


def generate_local_response(user_message: str, conversation: AssistantConversation | None = None) -> AssistantResponse:
    message = user_message.strip()
    lower = message.lower()

    # TODO: Replace this with an OpenAI conversation engine.
    # TODO: Extract explicit/implicit preferences from chat content.
    # TODO: Ask user permission before saving learned preferences to profiles.
    # TODO: Link assistant messages to user profiles for personalized context.
    # TODO: Add voice input/output support.
    if lower.startswith("my name is"):
        name = message[10:].strip() or "there"
        content = f"Thanks {name}. I can use that to help build your profile once profile learning is enabled."
    elif "light" in lower and ("like" in lower or "prefer" in lower):
        content = "Noted as a possible lighting preference. In a later step I can ask to save this to your profile."
    else:
        content = "Got it. I can help manage the home and track preferences once profile learning is enabled."

    response = AssistantResponse(message=AssistantMessage(role="assistant", content=content))
    if conversation is not None:
        conversation.messages.append(AssistantMessage(role="user", content=message))
        conversation.messages.append(response.message)
    return response

