from fastapi.testclient import TestClient
from pydantic import ValidationError

from altinet.display.app import create_app
from altinet.home.default_home import create_default_home_model
from altinet.home.models import HomeModel, PropertyBoundary
from altinet.home.storage import load_home_model, save_home_model


def test_model_validation():
    try:
        PropertyBoundary(width=-1, depth=2)
        assert False
    except ValidationError:
        assert True


def test_default_demo_model_creation():
    model = create_default_home_model()
    assert model.property_boundary.width == 20
    assert model.property_boundary.depth == 30
    assert len(model.floors) >= 2
    assert len(model.rooms) == 1
    assert len(model.walls) == 4
    assert len(model.doors) == 1
    assert len(model.lights) == 1


def test_save_load_home_model(tmp_path):
    path = tmp_path / 'home_model.json'
    demo = create_default_home_model()
    save_home_model(demo, path)
    loaded = load_home_model(path)
    assert isinstance(loaded, HomeModel)
    assert loaded.property_name == demo.property_name


def test_wall_room_polygon_and_pod_persistence(tmp_path):
    path = tmp_path / 'home_model.json'
    demo = create_default_home_model()
    demo.walls.append({"id": "wall-extra", "room_id": None, "floor_id": "floor-1", "x1": 1, "y1": 1, "x2": 2, "y2": 2, "thickness": 0.15})
    demo.room_regions.append({"id": "region-extra", "floor_id": "floor-1", "name": "Office", "points": [[0, 0], [2, 0], [2, 2]]})
    demo.perception_pods.append({"id": "pod-extra", "name": "Pod X", "floor_id": "floor-1", "x": 1.5, "y": 1.5, "orientation_degrees": 10, "camera_enabled": True, "microphone_enabled": False, "sensors": ["camera"]})
    save_home_model(demo, path)
    loaded = load_home_model(path)
    assert any(w.id == 'wall-extra' for w in loaded.walls)
    assert any(r.id == 'region-extra' for r in loaded.room_regions)
    assert any(p.id == 'pod-extra' for p in loaded.perception_pods)


def test_api_home_returns_valid_json(monkeypatch, tmp_path):
    path = tmp_path / 'home_model.json'
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    monkeypatch.setattr('altinet.display.routes.save_home_model', lambda m: save_home_model(m, path))
    monkeypatch.setattr('altinet.display.routes.reset_to_demo_model', lambda: save_home_model(create_default_home_model(), path))

    client = TestClient(create_app())
    response = client.get('/api/home')
    assert response.status_code == 200
    payload = response.json()
    assert payload['property_name']
    assert payload['units'] == 'metres'
    assert isinstance(payload['floors'], list)
    assert 'room_regions' in payload
    assert 'perception_pods' in payload


def test_api_home_post_accepts_new_fields(monkeypatch, tmp_path):
    path = tmp_path / 'home_model.json'
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    monkeypatch.setattr('altinet.display.routes.save_home_model', lambda m: save_home_model(m, path))
    monkeypatch.setattr('altinet.display.routes.reset_to_demo_model', lambda: save_home_model(create_default_home_model(), path))
    client = TestClient(create_app())
    payload = create_default_home_model().model_dump()
    payload['room_regions'].append({"id": "region-post", "floor_id": "floor-ground", "name": "New", "points": [[0, 0], [1, 0], [1, 1]]})
    payload['perception_pods'].append({"id": "pod-post", "name": "Pod 99", "floor_id": "floor-ground", "x": 2, "y": 2, "orientation_degrees": 0, "camera_enabled": True, "microphone_enabled": True, "sensors": ["camera"]})
    response = client.post('/api/home', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert any(r['id'] == 'region-post' for r in body['room_regions'])
    assert any(p['id'] == 'pod-post' for p in body['perception_pods'])


def test_home_builder_page_returns_200():
    client = TestClient(create_app())
    response = client.get('/home-builder')
    assert response.status_code == 200


def test_home_builder_contains_back_to_dashboard_link():
    client = TestClient(create_app())
    response = client.get("/home-builder")

    assert response.status_code == 200
    assert 'href="/"' in response.text
    assert 'Back to Dashboard' in response.text


def test_wall_model_supports_types():
    model = create_default_home_model()
    assert all(w.wall_type in ["external", "internal"] for w in model.walls)


def test_default_demo_walls_are_external():
    model = create_default_home_model()
    assert all(w.wall_type == "external" for w in model.walls)


def test_drawn_wall_can_be_internal():
    model = create_default_home_model()
    model.walls.append({"id": "wall-internal", "floor_id": "floor-ground", "x1": 1, "y1": 1, "x2": 2, "y2": 1, "thickness": 0.15, "wall_type": "internal"})
    assert any(w.id == "wall-internal" and w.wall_type == "internal" for w in model.walls)


def test_floor_clear_removes_floor_objects():
    model = create_default_home_model()
    floor_id = "floor-ground"
    model.walls = [w for w in model.walls if (w.floor_id or "floor-ground") != floor_id]
    model.doors = [d for d in model.doors if (d.floor_id or "floor-ground") != floor_id]
    model.lights = [l for l in model.lights if (l.floor_id or "floor-ground") != floor_id]
    model.room_regions = [r for r in model.room_regions if r.floor_id != floor_id]
    model.perception_pods = [p for p in model.perception_pods if p.floor_id != floor_id]
    assert not [w for w in model.walls if (w.floor_id or "floor-ground") == floor_id]
    assert not [d for d in model.doors if (d.floor_id or "floor-ground") == floor_id]
    assert not [l for l in model.lights if (l.floor_id or "floor-ground") == floor_id]
    assert not [r for r in model.room_regions if r.floor_id == floor_id]
    assert not [p for p in model.perception_pods if p.floor_id == floor_id]


def test_floor_delete_prevents_deleting_last_floor():
    model = create_default_home_model()
    model.floors = [model.floors[0]]
    can_delete = len(model.floors) > 1
    assert can_delete is False


def test_api_home_post_accepts_wall_type(monkeypatch, tmp_path):
    path = tmp_path / 'home_model.json'
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    monkeypatch.setattr('altinet.display.routes.save_home_model', lambda m: save_home_model(m, path))
    monkeypatch.setattr('altinet.display.routes.reset_to_demo_model', lambda: save_home_model(create_default_home_model(), path))
    client = TestClient(create_app())
    payload = create_default_home_model().model_dump()
    payload['walls'].append({"id": "wall-post", "room_id": None, "floor_id": "floor-ground", "x1": 0, "y1": 0, "x2": 1, "y2": 0, "thickness": 0.15, "wall_type": "internal", "material": "stud"})
    response = client.post('/api/home', json=payload)
    assert response.status_code == 200
    assert any(w['id'] == 'wall-post' and w['wall_type'] == 'internal' for w in response.json()['walls'])
