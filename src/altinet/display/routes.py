"""Routes for the LocalNode dashboard UI and state API."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from altinet.display.state_adapter import build_dashboard_state
from altinet.assistant.openai_engine import chat_with_ahlan
from altinet.home.models import HomeModel, HomeLocation
from altinet.home.storage import load_home_model, reset_to_blank_model, reset_to_demo_model, save_home_model
from altinet.domain.users import UserProfile
from altinet.domain.access import AccessLevel
from altinet.domain.context import UserPreference, UserRoutine, UserContext
from altinet.store.registry import RegistryService
from altinet.services.geocoding import validate_or_geocode_home_address
from altinet.services.weather import fetch_open_meteo_current_weather
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


@router.get("/settings")
def settings(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html", context={})


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
        "registry_available": True,
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




@router.get("/api/home/location")
def get_home_location() -> dict:
    return load_home_model().location.model_dump()


@router.post("/api/home/location")
def save_home_location(payload: HomeLocation) -> dict:
    model = load_home_model()
    model.location = payload
    return save_home_model(model).location.model_dump()


@router.post("/api/home/location/verify")
def verify_home_location() -> dict:
    model = load_home_model()
    result = validate_or_geocode_home_address(model.location.model_dump())
    if result.get("success"):
        for key, value in result.items():
            if hasattr(model.location, key):
                setattr(model.location, key, value)
        save_home_model(model)
    return result


@router.get("/api/weather/current")
def get_current_weather() -> dict:
    try:
        model = load_home_model()
    except FileNotFoundError:
        return {
            "available": False,
            "message": "Set and verify home address first.",
            "reason": "no_home_location_file",
            "location_debug": {"address_verified": False, "latitude": None, "longitude": None},
        }
    loc = model.location
    debug = {"address_verified": bool(loc.address_verified), "latitude": loc.latitude, "longitude": loc.longitude}
    if not loc.address_verified:
        return {"available": False, "message": "Set and verify home address first.", "reason": "address_not_verified", "location_debug": debug}
    if loc.latitude is None or loc.longitude is None:
        return {"available": False, "message": "Set and verify home address first.", "reason": "missing_lat_lon", "location_debug": debug}
    try:
        weather = fetch_open_meteo_current_weather(loc.latitude, loc.longitude)
        location_name = loc.suburb_city or _location_from_formatted_address(loc.formatted_address) or "Unknown location"
        return {
            **weather,
            "location_name": location_name,
            "formatted_address": loc.formatted_address,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "message": f"Unable to fetch weather right now: {exc}", "reason": "weather_fetch_failed", "location_debug": debug}


@router.get("/api/settings")
def get_settings() -> dict:
    return {
        "openai": {"configured": bool(os.getenv("OPENAI_API_KEY", "").strip()), "model": os.getenv("AHLAN_MODEL", "gpt-5.5-mini")},
        "google_maps": {"configured": bool(os.getenv("GOOGLE_MAPS_API_KEY", "").strip())},
        "weather": {"provider": os.getenv("WEATHER_PROVIDER", "open_meteo")},
        "perception": {
            "default_camera_index": int(os.getenv("DEFAULT_CAMERA_INDEX", "0")),
            "save_timestamped_captures": os.getenv("SAVE_TIMESTAMPED_CAPTURES", "true").lower() in {"1", "true", "yes", "on"},
        },
        "runtime": {"tick_rate_hz": float(os.getenv("RUNTIME_TICK_RATE_HZ", "1.0"))},
        "data": {"data_dir": os.getenv("ALTINET_DATA_DIR", "data/altinet")},
    }


def _location_from_formatted_address(formatted_address: str | None) -> str | None:
    if not formatted_address:
        return None
    parts = [p.strip() for p in formatted_address.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[1]
    return parts[0] if parts else None

@router.get("/api/registry")
def get_registry() -> dict:
    return RegistryService().load_registry()


@router.get("/api/users")
def get_users() -> list[dict]:
    return [profile.model_dump(mode="json") for profile in list_repo_users()]


@router.post("/api/users")
def create_user(payload: UserCreateRequest) -> dict:
    return create_repo_user(_build_user_profile(payload)).model_dump(mode="json")


@router.post("/api/registry/seed-demo")
def seed_demo_registry_users() -> dict:
    demo_profiles = [
        UserCreateRequest(display_name="Elliot", preferred_name="Elliot", access_level=AccessLevel.RESIDENT_OWNER, relationship_to_home="owner", contextual_information="Primary resident and decision maker."),
        UserCreateRequest(display_name="Mia", preferred_name="Mia", access_level=AccessLevel.RESIDENT_STANDARD, relationship_to_home="resident", contextual_information="Often in bedroom during bedtime routine."),
        UserCreateRequest(display_name="Guest Family", access_level=AccessLevel.GUEST_FAMILY, relationship_to_home="guest"),
    ]
    created = 0
    existing_names = {u.display_name for u in list_repo_users()}
    for profile in demo_profiles:
        if profile.display_name in existing_names:
            continue
        create_repo_user(_build_user_profile(profile))
        created += 1
    users = [u.model_dump(mode="json") for u in list_repo_users()]
    return {"ok": True, "message": "Demo data seeded", "users_count": len(users), "created": created, "users": users}


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




class UserCreateRequest(BaseModel):
    display_name: str = Field(min_length=1)
    access_level: AccessLevel = AccessLevel.RESIDENT_STANDARD
    preferred_name: str | None = None
    relationship_to_home: str | None = None
    notes: str | None = None
    contextual_information: str | None = None


def _build_user_profile(payload: UserCreateRequest) -> UserProfile:
    context_items = []
    if payload.contextual_information:
        context_items.append(UserContext(summary=payload.contextual_information))
    return UserProfile(
        display_name=payload.display_name,
        access_level=payload.access_level,
        preferred_name=payload.preferred_name,
        relationship_to_home=payload.relationship_to_home,
        notes=payload.notes or "",
        contextual_information=context_items,
    )

class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1)
    user_id: str | None = None
    recent_messages: list[dict] = Field(default_factory=list)


@router.get("/api/assistant/status")
def assistant_status() -> dict:
    api_key_configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    model = os.getenv("AHLAN_MODEL", "gpt-5.5-mini")
    return {
        "openai_configured": api_key_configured,
        "model": model,
        "engine": "openai" if api_key_configured else "local_fallback",
        "reason": None if api_key_configured else "OPENAI_API_KEY missing",
    }


@router.post("/api/assistant/chat")
def assistant_chat(payload: AssistantChatRequest) -> dict:
    result = chat_with_ahlan(payload.message, user_id=payload.user_id, recent_messages=payload.recent_messages)
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
