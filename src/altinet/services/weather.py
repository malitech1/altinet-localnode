from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch_open_meteo_current_weather(latitude: float, longitude: float) -> dict:
    query = urlencode({"latitude": latitude, "longitude": longitude, "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,wind_speed_10m,weather_code"})
    url = f"https://api.open-meteo.com/v1/forecast?{query}"
    with urlopen(url, timeout=10) as response:
        payload = json.loads(response.read().decode("utf-8"))

    current = payload.get("current", {})
    return {
        "available": True,
        "latitude": latitude,
        "longitude": longitude,
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation") if current.get("precipitation") is not None else current.get("rain"),
        "rain": current.get("rain"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "weather_description": _weather_code_to_description(current.get("weather_code")),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "provider": "open_meteo",
    }


def _weather_code_to_description(code: int | None) -> str:
    descriptions = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 61: "Rain", 63: "Moderate rain", 65: "Heavy rain", 71: "Snow", 95: "Thunderstorm"}
    return descriptions.get(code, "Unknown")
