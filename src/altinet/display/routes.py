"""Routes for the LocalNode dashboard UI and state API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
RUNTIME_STATE_PATH = DATA_DIR / "runtime" / "runtime_state.json"
ROOM_CONTEXT_PATH = DATA_DIR / "context" / "latest_room_context.json"
CAPTURE_PATH = DATA_DIR / "captures" / "latest.jpg"

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


@router.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@router.get("/api/state")
def get_state() -> dict:
    runtime_state = _read_json(RUNTIME_STATE_PATH)
    room_context = _read_json(ROOM_CONTEXT_PATH)

    if runtime_state:
        recent_events = runtime_state.get("recent_events", [])
        latest_decision = runtime_state.get("latest_decision")
        perception_summary = runtime_state.get("perception_summary")
        system_status = runtime_state.get("status", "running")
    else:
        recent_events = []
        latest_decision = None
        perception_summary = None
        system_status = "waiting_for_runtime"

    return {
        "title": "Altinet LocalNode",
        "current_time": datetime.now(timezone.utc).isoformat(),
        "system_status": system_status,
        "runtime_state": runtime_state,
        "room_context": room_context,
        "capture_available": CAPTURE_PATH.exists(),
        "recent_events": recent_events,
        "latest_decision": latest_decision,
        "decision_explanation": latest_decision.get("rationale") if isinstance(latest_decision, dict) else None,
        "perception_summary": perception_summary,
    }


@router.get("/captures/latest.jpg")
def latest_capture() -> FileResponse:
    if not CAPTURE_PATH.exists():
        raise HTTPException(status_code=404, detail="No captured image available yet.")
    return FileResponse(CAPTURE_PATH)
