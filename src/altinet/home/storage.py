import json
from pathlib import Path

from altinet.home.default_home import create_blank_home_model, create_default_home_model
from altinet.home.models import HomeModel

HOME_MODEL_PATH = Path(__file__).resolve().parents[3] / "data" / "home" / "home_model.json"


def save_home_model(model: HomeModel, path: Path = HOME_MODEL_PATH) -> HomeModel:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    return model


def load_home_model(path: Path = HOME_MODEL_PATH) -> HomeModel:
    if not path.exists():
        model = create_blank_home_model()
        save_home_model(model, path)
        return model
    payload = json.loads(path.read_text(encoding="utf-8"))
    location = payload.get("location")
    if isinstance(location, dict):
        if location.get("latitude") is None and location.get("lat") is not None:
            location["latitude"] = location.get("lat")
        if location.get("longitude") is None:
            if location.get("lon") is not None:
                location["longitude"] = location.get("lon")
            elif location.get("lng") is not None:
                location["longitude"] = location.get("lng")
        if "address_verified" not in location:
            for key in ("verified", "is_verified"):
                if key in location:
                    location["address_verified"] = bool(location.get(key))
                    break
    return HomeModel.model_validate(payload)


def reset_to_demo_model(path: Path = HOME_MODEL_PATH) -> HomeModel:
    return save_home_model(create_default_home_model(), path)


def reset_to_blank_model(path: Path = HOME_MODEL_PATH) -> HomeModel:
    return save_home_model(create_blank_home_model(), path)
