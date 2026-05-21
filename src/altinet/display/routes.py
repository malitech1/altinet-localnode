"""Routes for the LocalNode dashboard UI and state API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from altinet.display.state_adapter import build_dashboard_state
from altinet.home.models import HomeModel
from altinet.home.storage import load_home_model, reset_to_blank_model, reset_to_demo_model, save_home_model
from altinet.users.models import UserProfile
from altinet.users.storage import create_user_profile, delete_user_profile, load_user_profiles, update_user_profile

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


@router.get("/home-builder")
def home_builder(request: Request):
    return templates.TemplateResponse(request=request, name="home_builder.html", context={})


@router.get("/api/home")
def get_home() -> dict:
    return load_home_model().model_dump()


@router.post("/api/home")
def save_home(payload: HomeModel) -> dict:
    return save_home_model(payload).model_dump()


@router.post("/api/home/reset-demo")
def reset_demo() -> dict:
    return reset_to_demo_model().model_dump()


@router.post("/api/home/new-blank")
def new_blank_home() -> dict:
    return reset_to_blank_model().model_dump()


@router.get("/api/users")
def get_users() -> list[dict]:
    return [profile.model_dump(mode="json") for profile in load_user_profiles()]


@router.post("/api/users")
def create_user(payload: UserProfile) -> dict:
    return create_user_profile(payload).model_dump(mode="json")


@router.get("/api/users/{user_id}")
def get_user(user_id: str) -> dict:
    for profile in load_user_profiles():
        if profile.id == user_id:
            return profile.model_dump(mode="json")
    raise HTTPException(status_code=404, detail="User not found")


@router.patch("/api/users/{user_id}")
def patch_user(user_id: str, updates: dict) -> dict:
    updated = update_user_profile(user_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.model_dump(mode="json")


@router.delete("/api/users/{user_id}")
def remove_user(user_id: str) -> dict:
    deleted = delete_user_profile(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True, "user_id": user_id}
