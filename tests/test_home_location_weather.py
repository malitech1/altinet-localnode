import json
from fastapi.testclient import TestClient

from altinet.display.app import create_app
from altinet.home.default_home import create_blank_home_model
from altinet.home.storage import save_home_model, load_home_model


def test_save_home_location(monkeypatch, tmp_path):
    path = tmp_path / 'home.json'
    save_home_model(create_blank_home_model(), path)
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    monkeypatch.setattr('altinet.display.routes.save_home_model', lambda m: save_home_model(m, path))
    client = TestClient(create_app())
    payload = {"address_line_1": "1 Main St", "address_line_2": "", "suburb_city": "Austin", "state_region": "TX", "postcode": "78701", "country": "US"}
    r = client.post('/api/home/location', json=payload)
    assert r.status_code == 200
    assert r.json()['address_line_1'] == '1 Main St'


def test_verify_location_with_mocked_google(monkeypatch, tmp_path):
    path = tmp_path / 'home.json'
    model = create_blank_home_model()
    model.location.address_line_1='1 Main St'; model.location.suburb_city='Austin'; model.location.state_region='TX'; model.location.postcode='78701'; model.location.country='US'
    save_home_model(model, path)
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    monkeypatch.setattr('altinet.display.routes.save_home_model', lambda m: save_home_model(m, path))
    monkeypatch.setattr('altinet.display.routes.validate_or_geocode_home_address', lambda _: {"success": True, "message":"Address verified", "formatted_address":"1 Main St, Austin TX", "latitude":30.0, "longitude":-97.0, "google_place_id":"abc", "address_verified":True, "address_verification_source":"google_maps", "address_verified_at":"now"})
    client = TestClient(create_app())
    r = client.post('/api/home/location/verify')
    assert r.status_code == 200
    assert r.json()['success'] is True
    assert r.json()['address_verified'] is True
    assert r.json()['formatted_address'] == '1 Main St, Austin TX'
    assert r.json()['latitude'] == 30.0
    assert r.json()['longitude'] == -97.0
    saved = load_home_model(path)
    assert saved.location.address_verified is True
    assert saved.location.latitude == 30.0
    assert saved.location.longitude == -97.0


def test_missing_google_key_returns_clean_error(monkeypatch):
    monkeypatch.delenv('GOOGLE_MAPS_API_KEY', raising=False)
    from altinet.services.geocoding import geocode_address
    result = geocode_address('x')
    assert result.success is False
    assert 'not configured' in result.message


def test_weather_unavailable_without_location(monkeypatch, tmp_path):
    path = tmp_path / 'home.json'
    save_home_model(create_blank_home_model(), path)
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    client = TestClient(create_app())
    r = client.get('/api/weather/current')
    assert r.json()['available'] is False
    assert r.json()['reason'] == 'address_not_verified'


def test_weather_with_mocked_open_meteo(monkeypatch, tmp_path):
    path = tmp_path / 'home.json'
    m = create_blank_home_model(); m.location.address_verified=True; m.location.latitude=30.0; m.location.longitude=-97.0
    save_home_model(m, path)
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    called = {}
    def _mock_fetch(lat, lon):
        called['lat'] = lat
        called['lon'] = lon
        return {"available": True, "temperature": 21, "apparent_temperature": 22, "humidity": 50, "precipitation": 0.2, "wind_speed": 5, "weather_code": 1, "weather_description":"Mainly clear", "fetched_at":"now"}
    monkeypatch.setattr('altinet.display.routes.fetch_open_meteo_current_weather', _mock_fetch)
    client = TestClient(create_app())
    r = client.get('/api/weather/current')
    assert r.json()['available'] is True
    assert called == {"lat": 30.0, "lon": -97.0}


def test_weather_reason_missing_lat_lon(monkeypatch, tmp_path):
    path = tmp_path / 'home.json'
    m = create_blank_home_model(); m.location.address_verified=True
    save_home_model(m, path)
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    client = TestClient(create_app())
    r = client.get('/api/weather/current')
    assert r.json()['available'] is False
    assert r.json()['reason'] == 'missing_lat_lon'


def test_weather_reason_address_not_verified(monkeypatch, tmp_path):
    path = tmp_path / 'home.json'
    m = create_blank_home_model(); m.location.address_verified=False; m.location.latitude=30.0; m.location.longitude=-97.0
    save_home_model(m, path)
    monkeypatch.setattr('altinet.display.routes.load_home_model', lambda: load_home_model(path))
    client = TestClient(create_app())
    r = client.get('/api/weather/current')
    assert r.json()['available'] is False
    assert r.json()['reason'] == 'address_not_verified'


def test_dashboard_contains_home_location_and_weather_cards():
    client = TestClient(create_app())
    body = client.get('/').text
    assert 'Home Location' in body
    assert 'Weather' in body


def test_dashboard_js_calls_load_weather_after_address_verification():
    js = open('src/altinet/display/static/dashboard.js', encoding='utf-8').read()
    assert 'Verifying address...' in js
    assert 'await loadHomeLocation();' in js
    assert 'await loadWeather();' in js


def test_load_home_model_normalizes_legacy_location_fields(tmp_path):
    path = tmp_path / 'home.json'
    payload = create_blank_home_model().model_dump()
    payload["location"] = {"lat": -27.6113215, "lng": 153.3701154, "verified": True}
    path.write_text(json.dumps(payload), encoding='utf-8')
    model = load_home_model(path)
    assert model.location.address_verified is True
    assert model.location.latitude == -27.6113215
    assert model.location.longitude == 153.3701154
