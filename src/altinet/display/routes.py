"""Routes for the LocalNode dashboard UI and state API."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from altinet.display.state_adapter import build_dashboard_state
from altinet.assistant.openai_engine import chat_with_ahlan
from altinet.home.models import HomeModel
from altinet.home.storage import load_home_model, reset_to_blank_model, reset_to_demo_model, save_home_model
from altinet.domain.users import UserProfile
from altinet.domain.context import UserPreference, UserRoutine, UserContext
from altinet.store.registry import RegistryService
from altinet.store.repositories.users_repository import (
    add_context_note,
    add_preference,
    add_routine,
    create_user as create_repo_user,
    delete_user as delete_repo_user,
    get_user as get_repo_user,
    list_users as list_repo_users,
    update_user as update_repo_user,
)

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

    registry = RegistryService().load_registry()
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
        "registry": registry,
        "users": registry.get("users", []),
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


@router.get("/api/registry")
def get_registry() -> dict:
    return RegistryService().load_registry()


@router.get("/api/users")
def get_users() -> list[dict]:
    return [profile.model_dump(mode="json") for profile in list_repo_users()]


@router.post("/api/users")
def create_user(payload: UserProfile) -> dict:
    return create_repo_user(payload).model_dump(mode="json")


@router.get("/api/users/{user_id}")
def get_user(user_id: str) -> dict:
    profile = get_repo_user(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User not found")
    return profile.model_dump(mode="json")


@router.patch("/api/users/{user_id}")
def patch_user(user_id: str, updates: dict) -> dict:
    updated = update_repo_user(user_id, updates)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.model_dump(mode="json")


@router.delete("/api/users/{user_id}")
def remove_user(user_id: str) -> dict:
    deleted = delete_repo_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"deleted": True, "user_id": user_id}


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str | None = None


@router.post("/api/assistant/chat")
def assistant_chat(payload: AssistantChatRequest) -> dict:
    result = chat_with_ahlan(payload.message, user_id=payload.user_id, recent_messages=[])
    return result.model_dump()


@router.post("/api/users/{user_id}/preferences")
def create_user_preference(user_id: str, payload: UserPreference) -> dict:
    updated = add_preference(user_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.model_dump(mode="json")


@router.post("/api/users/{user_id}/routines")
def create_user_routine(user_id: str, payload: UserRoutine) -> dict:
    updated = add_routine(user_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.model_dump(mode="json")


@router.post("/api/users/{user_id}/context-notes")
def create_user_context_note(user_id: str, payload: UserContext) -> dict:
    updated = add_context_note(user_id, payload)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.model_dump(mode="json")
