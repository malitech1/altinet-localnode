from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


@dataclass
class GeocodingResult:
    success: bool
    message: str
    formatted_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = None
    source: str = "google_maps"


def geocode_address(address: str) -> GeocodingResult:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return GeocodingResult(success=False, message="Google Maps API key is not configured")
    query = urlencode({"address": address, "key": api_key})
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{query}"
    try:
        with urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return GeocodingResult(success=False, message=f"Google geocoding failed: {exc}")

    if payload.get("status") != "OK" or not payload.get("results"):
        return GeocodingResult(success=False, message=f"Google geocoding failed: {payload.get('status', 'unknown error')}")

    result = payload["results"][0]
    location = result.get("geometry", {}).get("location", {})
    return GeocodingResult(
        success=True,
        message="Address verified",
        formatted_address=result.get("formatted_address"),
        latitude=location.get("lat"),
        longitude=location.get("lng"),
        place_id=result.get("place_id"),
    )


def validate_or_geocode_home_address(home_address: dict[str, Any]) -> dict[str, Any]:
    address_parts = [home_address.get("address_line_1"), home_address.get("address_line_2"), home_address.get("suburb_city"), home_address.get("state_region"), home_address.get("postcode"), home_address.get("country")]
    address = ", ".join([part.strip() for part in address_parts if isinstance(part, str) and part.strip()])
    if not address:
        return {"success": False, "message": "Address fields are required before verification."}

    result = geocode_address(address)
    if not result.success:
        return {"success": False, "message": result.message, "address_verified": False, "address_verification_source": result.source}

    return {
        "success": True,
        "message": result.message,
        "formatted_address": result.formatted_address,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "google_place_id": result.place_id,
        "address_verified": True,
        "address_verification_source": result.source,
        "address_verified_at": datetime.now(timezone.utc).isoformat(),
    }
