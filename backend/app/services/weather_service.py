"""Weather data integration using Open-Meteo (fully free, no API key required).

Falls back gracefully if the service is unavailable.
"""

import logging
import time
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory cache: (lat_round, lon_round) -> (timestamp, data)
_cache: dict[tuple[float, float], tuple[float, dict]] = {}
CACHE_TTL = settings.WEATHER_CACHE_TTL_SECONDS


@dataclass
class WeatherData:
    condition: str
    temperature_f: float
    visibility_miles: float | None
    wind_speed_mph: float
    humidity: int
    road_condition: str

    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "temperature_f": self.temperature_f,
            "visibility_miles": self.visibility_miles,
            "wind_speed_mph": self.wind_speed_mph,
            "humidity": self.humidity,
            "road_condition": self.road_condition,
        }


async def get_weather(lat: float, lon: float) -> dict | None:
    """Fetch current weather for a location. Returns dict or None on failure."""
    # Round coordinates for cache key (weather doesn't vary at sub-km scale)
    cache_key = (round(lat, 2), round(lon, 2))
    now = time.time()

    # Check cache
    if cache_key in _cache:
        cached_time, cached_data = _cache[cache_key]
        if now - cached_time < CACHE_TTL:
            return cached_data

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,visibility"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )

        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        current = data.get("current", {})

        # Map WMO weather codes to conditions
        wmo_code = current.get("weather_code", 0)
        condition = _wmo_to_condition(wmo_code)

        temp_f = current.get("temperature_2m", 70)
        visibility_m = current.get("visibility", 10000)
        visibility_miles = round(visibility_m / 1609.34, 1) if visibility_m else None
        wind_speed = current.get("wind_speed_10m", 0)
        humidity = current.get("relative_humidity_2m", 50)

        # Infer road condition
        road_condition = "dry"
        if condition in ("rain", "heavy_rain", "freezing_rain"):
            road_condition = "wet"
        elif condition in ("snow", "heavy_snow"):
            road_condition = "snowy"
        elif temp_f < 32:
            road_condition = "possibly_icy"

        weather = WeatherData(
            condition=condition,
            temperature_f=temp_f,
            visibility_miles=visibility_miles,
            wind_speed_mph=wind_speed,
            humidity=humidity,
            road_condition=road_condition,
        )

        result = weather.to_dict()
        _cache[cache_key] = (now, result)
        return result

    except Exception as e:
        logger.warning("Weather fetch failed for (%.2f, %.2f): %s", lat, lon, e)
        return None


def _wmo_to_condition(code: int) -> str:
    """Convert WMO weather code to a human-readable condition string."""
    if code == 0:
        return "clear"
    elif code in (1, 2, 3):
        return "partly_cloudy"
    elif code in (45, 48):
        return "fog"
    elif code in (51, 53, 55, 56, 57):
        return "drizzle"
    elif code in (61, 63, 80, 81):
        return "rain"
    elif code in (65, 82):
        return "heavy_rain"
    elif code in (66, 67):
        return "freezing_rain"
    elif code in (71, 73, 75, 77, 85, 86):
        return "snow"
    elif code in (95, 96, 99):
        return "thunderstorm"
    return "unknown"
