from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field
from altinet.core.ids import new_id


class AgentProfile(BaseModel):
    id: str = Field(default_factory=lambda: new_id("agent"))
    name: str
    agent_type: Literal["software_agent", "robot", "perception_pod", "appliance_node", "localnode_service"]
    location: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    status: str = "active"
    permissions: list[str] = Field(default_factory=list)
    notes: str = ""
