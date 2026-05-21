"""Build complete decision prompts for the LLM."""

from __future__ import annotations

import json
from collections.abc import Iterable

from altinet.context.contextualiser import build_context_block
from altinet.context.schemas import HouseState, PossibleAction


DEFAULT_SYSTEM_ROLE = (
    "You are Altinet Decision Engine, a careful and safety-first home automation assistant. "
    "Choose exactly one action from the provided list based on resident comfort, context, and minimal disruption."
)

DEFAULT_HOUSE_RULES = [
    "Prioritise resident safety and comfort over automation convenience.",
    "At night, avoid leaving occupied rooms in darkness.",
    "If context is ambiguous, choose the least intrusive safe action.",
]

REQUIRED_RESPONSE_SCHEMA = {
    "selected_action": "<one of possible_actions>",
    "rationale": "<brief explanation grounded in context>",
}


def build_decision_prompt(
    house_state: HouseState,
    possible_actions: Iterable[PossibleAction | str],
    *,
    system_role: str = DEFAULT_SYSTEM_ROLE,
    house_rules: Iterable[str] | None = None,
    resident_background: str = "No extra resident background provided.",
    recent_events: Iterable[str] | None = None,
) -> str:
    """Build a complete prompt string ready to send to an LLM."""
    normalised_actions = [str(action) for action in possible_actions]
    rules = list(house_rules) if house_rules is not None else DEFAULT_HOUSE_RULES
    current_context = build_context_block(house_state=house_state, recent_events=recent_events)

    prompt_sections = [
        "# System Role",
        system_role.strip(),
        "",
        "# House Rules",
        _format_bullets(rules),
        "",
        "# Resident Background",
        resident_background.strip(),
        "",
        "# Current Context",
        current_context,
        "",
        "# Possible Actions",
        _format_bullets(normalised_actions),
        "",
        "# Required JSON Response Format",
        "Return only valid JSON with this exact shape:",
        json.dumps(REQUIRED_RESPONSE_SCHEMA, indent=2),
    ]

    return "\n".join(prompt_sections).strip() + "\n"


def _format_bullets(items: Iterable[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return "- (none)"
    return "\n".join(f"- {item}" for item in cleaned)
