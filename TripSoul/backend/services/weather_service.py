"""
Weather Service — OpenWeather API with automatic mock fallback.
Provides current conditions and rain probability for prediction & adaptation.
"""
import os
import httpx
from ..utils.mock_data import get_mock_weather

_OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")
_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# City -> lat/lng for API calls
_CITY_COORDS = {
    "nyc": (40.7128, -74.0060),
    "tokyo": (35.6762, 139.6503),
    "paris": (48.8566, 2.3522),
}


async def get_weather(city: str) -> dict:
    """Fetch current weather. Falls back to mock data if API key is absent or call fails."""
    key = city.lower().strip()

    if not _OPENWEATHER_KEY or len(_OPENWEATHER_KEY) < 20 or "mock" in _OPENWEATHER_KEY.lower():
        return get_mock_weather(key)

    coords = _CITY_COORDS.get(key)
    if not coords:
        return get_mock_weather(key)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(_BASE_URL, params={
                "lat": coords[0], "lon": coords[1],
                "appid": _OPENWEATHER_KEY, "units": "metric",
            })
            resp.raise_for_status()
            data = resp.json()

            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            rain = data.get("rain", {})

            return {
                "temp_c": main.get("temp", 20.0),
                "feels_like_c": main.get("feels_like", 20.0),
                "condition": weather.get("main", "Clear").lower().replace(" ", "_"),
                "description": weather.get("description", ""),
                "humidity": main.get("humidity", 50),
                "wind_kph": round(wind.get("speed", 0) * 3.6, 1),
                "rain_probability": 0.8 if rain else 0.1,
                "rain_mm": rain.get("1h", 0.0),
                "visibility_km": data.get("visibility", 10000) / 1000,
            }
    except Exception as e:
        print(f"[WEATHER] API error: {e} — using mock data")
        return get_mock_weather(key)


def is_rainy(weather: dict) -> bool:
    """Check if weather conditions indicate rain."""
    return (
        weather.get("rain_probability", 0) > 0.5
        or weather.get("rain_mm", 0) > 2.0
        or "rain" in weather.get("condition", "")
    )


def weather_impact_factor(weather: dict) -> float:
    """Return a multiplier [1.0..1.5] for travel time based on weather.
    1.0 = clear, 1.5 = heavy rain.
    """
    if is_rainy(weather):
        rain_mm = weather.get("rain_mm", 0)
        if rain_mm > 10:
            return 1.5
        elif rain_mm > 5:
            return 1.3
        return 1.2
    if weather.get("wind_kph", 0) > 30:
        return 1.15
    return 1.0
