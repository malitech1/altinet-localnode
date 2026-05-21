"""Normalize runtime/context state for dashboard consumption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOM_NAMES = [
    "Kitchen",
    "Dining Room",
    "Living Room",
    "Bedroom 1",
    "Bathroom",
    "Laundry",
    "Office",
    "Entry",
]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _titleize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").strip().title()


def build_dashboard_state(runtime_state_path: Path, room_context_path: Path, latest_decision_path: Path) -> dict[str, Any]:
    runtime_state = _read_json(runtime_state_path)
    room_context = _read_json(room_context_path)
    decision_file = _read_json(latest_decision_path)

    occupancy = runtime_state.get("current_room_occupancy", {}) if runtime_state else {}
    occupancy = occupancy if isinstance(occupancy, dict) else {}
    runtime_residents = runtime_state.get("active_residents", []) if runtime_state else []
    runtime_residents = runtime_residents if isinstance(runtime_residents, list) else []

    context_occupants = room_context.get("occupants", []) if room_context else []
    context_occupants = context_occupants if isinstance(context_occupants, list) else []

    residents: list[dict[str, Any]] = []
    for index, rid in enumerate(runtime_residents or context_occupants or ["resident_elliot", "resident_mia"]):
        name = _titleize(str(rid).removeprefix("resident_"))
        room = next((k for k, v in occupancy.items() if isinstance(v, list) and rid in v), None) or ROOM_NAMES[index % len(ROOM_NAMES)]
        residents.append({"id": str(rid), "name": name, "location": _titleize(room), "status": "home"})

    devices_dict = runtime_state.get("devices", {}) if runtime_state else {}
    devices_dict = devices_dict if isinstance(devices_dict, dict) else {}
    devices = [
        {
            "id": device_id,
            "name": _titleize(device_id),
            "state": "on" if bool(device.get("is_on")) else "off",
            "metadata": device.get("metadata", {}) if isinstance(device, dict) else {},
        }
        for device_id, device in devices_dict.items()
    ]

    agents = [{"id": "agent_r1", "name": "R1 - Atlas", "status": "monitoring"}] if not runtime_state else []

    latest_runtime_decision = runtime_state.get("latest_decision") if runtime_state else None
    decision_source = latest_runtime_decision if isinstance(latest_runtime_decision, dict) else decision_file
    decisions = []
    if isinstance(decision_source, dict):
        decisions.append(
            {
                "action": decision_source.get("action") or decision_source.get("selected_action") or "No action",
                "explanation": decision_source.get("explanation") or decision_source.get("rationale") or "No explanation available.",
                "impact": decision_source.get("impact") or "Impact not recorded.",
                "timestamp": decision_source.get("timestamp") or decision_source.get("time"),
            }
        )

    recent_events = runtime_state.get("recent_events", []) if runtime_state else []
    if isinstance(recent_events, list):
        for event in recent_events:
            if not isinstance(event, dict):
                continue
            action = event.get("action") or event.get("selected_action")
            if not action:
                continue
            decisions.append(
                {
                    "action": action,
                    "explanation": event.get("explanation") or event.get("rationale") or "No explanation available.",
                    "impact": event.get("impact") or "Impact not recorded.",
                    "timestamp": event.get("timestamp") or event.get("time"),
                }
            )
    decisions = decisions[:3]

    rooms = [{"name": room_name} for room_name in ROOM_NAMES]
    alerts = runtime_state.get("alerts", []) if runtime_state else []
    alerts = alerts if isinstance(alerts, list) else []
    perception = runtime_state.get("perception_summary") if runtime_state else None

    return {
        "runtime_state": runtime_state,
        "room_context": room_context,
        "residents": residents,
        "pets": room_context.get("pets", []) if room_context else [],
        "rooms": rooms,
        "devices": devices,
        "agents": agents,
        "decisions": decisions,
        "alerts": alerts,
        "perception": perception,
        "system_status": runtime_state.get("status", "waiting_for_runtime") if runtime_state else "waiting_for_runtime",
    }
