from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class AssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AssistantConversation(BaseModel):
    messages: list[AssistantMessage] = Field(default_factory=list)


class AssistantResponse(BaseModel):
    message: AssistantMessage

