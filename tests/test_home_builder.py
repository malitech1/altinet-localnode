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
