"""Prompt builder for decision-model input preparation."""

from altinet.context.schemas import HomeContext


def build_decision_prompt(context: HomeContext) -> str:
    """Return a simple structured prompt string from validated home context."""
    return (
        f"Home ID: {context.home_id}\n"
        f"Users: {[u.name for u in context.users]}\n"
        f"Rooms: {[r.name for r in context.rooms]}\n"
        f"Sensors: {[s.sensor_id for s in context.sensors]}\n"
        f"Possible actions: {[a.description for a in context.possible_actions]}"
    )
