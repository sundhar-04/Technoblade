"""
Shared utility functions for TripSoul backend.
"""
import math
from datetime import datetime


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance between two coordinates in kilometres."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def estimate_travel_minutes(distance_km: float, mode: str = "transit") -> int:
    """Estimate travel time based on distance and mode.
    Speeds: walking=5km/h, transit=25km/h, driving=35km/h.
    """
    speeds = {"walking": 5.0, "transit": 25.0, "driving": 35.0}
    speed = speeds.get(mode, 25.0)
    return max(5, int((distance_km / speed) * 60))


def time_str(hour: int, minute: int = 0) -> str:
    """Format hour:minute as 'HH:MM'."""
    return f"{hour:02d}:{minute:02d}"


def add_minutes(time_string: str, minutes: int) -> str:
    """Add minutes to a time string 'HH:MM', return new 'HH:MM'."""
    parts = time_string.split(":")
    h, m = int(parts[0]), int(parts[1])
    total = h * 60 + m + minutes
    return time_str(total // 60, total % 60)


def confidence_from_factors(
    popularity: float,
    weather_ok: bool = True,
    budget_fit: bool = True,
    interest_match: bool = True,
) -> float:
    """Compute a confidence score [0..1] from multiple factors."""
    score = popularity * 0.4
    if weather_ok:
        score += 0.2
    if budget_fit:
        score += 0.2
    if interest_match:
        score += 0.2
    return round(min(1.0, max(0.0, score)), 2)


def current_timestamp() -> str:
    """ISO timestamp string."""
    return datetime.utcnow().isoformat() + "Z"
