"""
Mock API responses for when external API keys are not configured.
Provides realistic data for weather, traffic, and places.
"""
import random

MOCK_WEATHER = {
    "nyc": {
        "temp_c": 22.0, "feels_like_c": 21.0,
        "condition": "partly_cloudy", "description": "Partly cloudy",
        "humidity": 55, "wind_kph": 15.0,
        "rain_probability": 0.15, "rain_mm": 0.0,
        "visibility_km": 10.0,
    },
    "tokyo": {
        "temp_c": 26.0, "feels_like_c": 28.0,
        "condition": "clear", "description": "Clear sky",
        "humidity": 65, "wind_kph": 8.0,
        "rain_probability": 0.10, "rain_mm": 0.0,
        "visibility_km": 12.0,
    },
    "paris": {
        "temp_c": 18.0, "feels_like_c": 17.0,
        "condition": "overcast", "description": "Overcast clouds",
        "humidity": 70, "wind_kph": 12.0,
        "rain_probability": 0.35, "rain_mm": 0.5,
        "visibility_km": 8.0,
    },
}

# Simulated disruption scenarios for demo
MOCK_DISRUPTIONS = {
    "weather": {
        "type": "weather",
        "severity": "high",
        "description": "Heavy rain forecast — 85% precipitation probability for the next 3 hours",
        "condition_override": {
            "condition": "heavy_rain", "description": "Heavy rain",
            "rain_probability": 0.85, "rain_mm": 12.0,
            "temp_c": 15.0, "humidity": 92, "wind_kph": 25.0,
        },
    },
    "closure": {
        "type": "closure",
        "severity": "medium",
        "description": "Unexpected venue closure due to maintenance",
    },
    "delay": {
        "type": "delay",
        "severity": "medium",
        "description": "Transit delay — estimated 40 min added to travel times in central zone",
    },
}


def get_mock_weather(city: str) -> dict:
    """Return mock weather for a city."""
    return MOCK_WEATHER.get(city.lower(), MOCK_WEATHER["nyc"]).copy()


def get_mock_disruption(disruption_type: str) -> dict:
    """Return a mock disruption scenario."""
    return MOCK_DISRUPTIONS.get(disruption_type, MOCK_DISRUPTIONS["weather"]).copy()


def get_mock_congestion(hour: int) -> float:
    """Return a congestion multiplier based on time of day.
    1.0 = normal, >1 = congested.
    """
    # Rush hours: 8-10, 17-19
    if 8 <= hour <= 10 or 17 <= hour <= 19:
        return 1.3 + random.uniform(0, 0.3)
    elif 11 <= hour <= 16:
        return 1.1 + random.uniform(0, 0.15)
    else:
        return 1.0 + random.uniform(0, 0.1)
