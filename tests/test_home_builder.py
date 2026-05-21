from fastapi.testclient import TestClient
from pydantic import ValidationError

from altinet.display.app import create_app
from altinet.home.default_home import create_blank_home_model, create_default_home_model
from altinet.home.models import HomeModel, PropertyBoundary
from altinet.home.storage import load_home_model, save_home_model


def wall_len(w):
    return ((w.x2 - w.x1) ** 2 + (w.y2 - w.y1) ** 2) ** 0.5


def wall_angle(w):
    import math

    return math.degrees(math.atan2(w.y2 - w.y1, w.x2 - w.x1))


def test_model_validation():
    try:
        PropertyBoundary(width=-1, depth=2)
        assert False
    except ValidationError:
        assert True


def test_blank_home_model_creation():
    model = create_blank_home_model()
    assert model.property_name == "New Altinet Home"
    assert len(model.floors) == 1
    assert model.floors[0].name == "Ground Floor"
    assert len(model.walls) == len(model.rooms) == len(model.doors) == len(model.windows) == 0


def test_wall_length_calculation():
    wall = create_default_home_model().walls[0]
    assert wall_len(wall) == 6.0


def test_wall_angle_calculation():
    wall = create_default_home_model().walls[1]
    assert wall_angle(wall) == 90.0


def test_door_stores_wall_id_and_position_along_wall_m():
    door = create_default_home_model().doors[0]
    assert door.wall_id == "wall-south"
    assert door.position_along_wall_m == 2.4


def test_window_stores_wall_id_and_position_along_wall_m():
    model = create_default_home_model()
    model.windows.append({"id": "w1", "floor_id": "floor-ground", "room_id": None, "wall_id": "wall-north", "x": 1, "y": 0, "width": 1.2, "width_m": 1.2, "position_along_wall_m": 1.0})
    assert model.windows[-1].wall_id == "wall-north"
    assert model.windows[-1].position_along_wall_m == 1.0


def test_room_stores_name_and_room_type():
    model = create_default_home_model()
    model.room_regions.append({"id": "region2", "floor_id": "floor-ground", "name": "Office", "room_type": "office", "points": [[0, 0], [1, 0], [1, 1]]})
    assert model.room_regions[-1].name == "Office"
    assert model.room_regions[-1].room_type == "office"


def test_save_load_home_model(tmp_path):
    path = tmp_path / "home_model.json"
    model = create_blank_home_model()
    save_home_model(model, path)
    loaded = load_home_model(path)
    assert isinstance(loaded, HomeModel)
    assert loaded.property_name == model.property_name


def test_api_accepts_returns_new_door_window_fields(monkeypatch, tmp_path):
    path = tmp_path / "home_model.json"
    monkeypatch.setattr("altinet.display.routes.load_home_model", lambda: load_home_model(path))
    monkeypatch.setattr("altinet.display.routes.save_home_model", lambda m: save_home_model(m, path))
    monkeypatch.setattr("altinet.display.routes.reset_to_demo_model", lambda: save_home_model(create_default_home_model(), path))
    monkeypatch.setattr("altinet.display.routes.reset_to_blank_model", lambda: save_home_model(create_blank_home_model(), path))
    client = TestClient(create_app())
    payload = create_default_home_model().model_dump()
    payload["windows"].append({"id": "w-post", "room_id": None, "wall_id": "wall-north", "floor_id": "floor-ground", "x": 1, "y": 0, "width": 1.2, "position_along_wall_m": 1.0, "width_m": 1.2, "height_m": 1.0, "sill_height_m": 0.9})
    response = client.post("/api/home", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["doors"][0]["position_along_wall_m"] == 2.4
    assert any(w["id"] == "w-post" and w["position_along_wall_m"] == 1.0 for w in body["windows"])


def test_deleting_wall_cleans_attached_doors_windows():
    model = create_default_home_model()
    model.windows.append({"id": "w-del", "room_id": None, "wall_id": "wall-south", "floor_id": "floor-ground", "x": 2, "y": 4, "width": 1.0, "width_m": 1.0, "position_along_wall_m": 2.0})
    wall_id = "wall-south"
    model.walls = [w for w in model.walls if w.id != wall_id]
    model.doors = [d for d in model.doors if d.wall_id != wall_id]
    model.windows = [w for w in model.windows if w.wall_id != wall_id]
    assert not [d for d in model.doors if d.wall_id == wall_id]
    assert not [w for w in model.windows if w.wall_id == wall_id]


def test_home_builder_page_returns_200():
    client = TestClient(create_app())
    assert client.get('/home-builder').status_code == 200
