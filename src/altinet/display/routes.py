"""Routes for the LocalNode dashboard UI and state API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from altinet.display.state_adapter import build_dashboard_state

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
RUNTIME_STATE_PATH = DATA_DIR / "runtime" / "runtime_state.json"
ROOM_CONTEXT_PATH = DATA_DIR / "context" / "latest_room_context.json"
LATEST_DECISION_PATH = DATA_DIR / "context" / "latest_decision.json"
CAPTURE_PATH = DATA_DIR / "captures" / "latest.jpg"

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@router.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={})


@router.get("/api/state")
def get_state() -> dict:
    normalized = build_dashboard_state(RUNTIME_STATE_PATH, ROOM_CONTEXT_PATH, LATEST_DECISION_PATH)
    latest_decision = normalized["decisions"][0] if normalized["decisions"] else None

    return {
        "title": "Altinet LocalNode",
        "current_time": datetime.now(timezone.utc).isoformat(),
        "capture_available": CAPTURE_PATH.exists(),
        **normalized,
        # Backward-compatible aliases for existing demos.
        "recent_events": normalized["runtime_state"].get("recent_events", []) if normalized["runtime_state"] else [],
        "latest_decision": latest_decision,
        "decision_explanation": latest_decision.get("explanation") if isinstance(latest_decision, dict) else None,
        "perception_summary": normalized["perception"],
    }


@router.get("/captures/latest.jpg")
def latest_capture() -> FileResponse:
    if not CAPTURE_PATH.exists():
        raise HTTPException(status_code=404, detail="No captured image available yet.")
    return FileResponse(CAPTURE_PATH)
