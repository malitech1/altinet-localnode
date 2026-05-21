import json
from pathlib import Path

from altinet.home.default_home import create_default_home_model
from altinet.home.models import HomeModel

HOME_MODEL_PATH = Path(__file__).resolve().parents[3] / "data" / "home" / "home_model.json"


def save_home_model(model: HomeModel, path: Path = HOME_MODEL_PATH) -> HomeModel:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    return model


def load_home_model(path: Path = HOME_MODEL_PATH) -> HomeModel:
    if not path.exists():
        model = create_default_home_model()
        save_home_model(model, path)
        return model
    payload = json.loads(path.read_text(encoding="utf-8"))
    return HomeModel.model_validate(payload)


def reset_to_demo_model(path: Path = HOME_MODEL_PATH) -> HomeModel:
    return save_home_model(create_default_home_model(), path)
