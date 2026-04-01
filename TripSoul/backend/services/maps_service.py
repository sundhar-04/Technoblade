"""
Maps Service — Google Maps/Distance Matrix with mock fallback.
Provides travel time and distance estimation between activities.
"""
import os
import httpx
from ..utils.helpers import haversine_km, estimate_travel_minutes

_GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
_DISTANCE_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


async def get_travel_info(
    origin_lat: float, origin_lng: float,
    dest_lat: float, dest_lng: float,
    mode: str = "transit",
) -> dict:
    """Get travel time and distance between two points.
    Uses Google Distance Matrix API if key is available, otherwise haversine estimate.
    """
    if _GOOGLE_MAPS_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(_DISTANCE_URL, params={
                    "origins": f"{origin_lat},{origin_lng}",
                    "destinations": f"{dest_lat},{dest_lng}",
                    "mode": mode if mode != "transit" else "transit",
                    "key": _GOOGLE_MAPS_KEY,
                })
                resp.raise_for_status()
                data = resp.json()

                element = data["rows"][0]["elements"][0]
                if element["status"] == "OK":
                    return {
                        "distance_km": element["distance"]["value"] / 1000,
                        "duration_minutes": element["duration"]["value"] // 60,
                        "source": "google_maps",
                    }
        except Exception as e:
            print(f"[MAPS] API error: {e} — using haversine estimate")

    # Mock fallback: haversine + urban travel factor
    straight_line = haversine_km(origin_lat, origin_lng, dest_lat, dest_lng)
    # Urban streets are ~1.4x straight-line distance
    road_distance = straight_line * 1.4
    travel_min = estimate_travel_minutes(road_distance, mode)

    return {
        "distance_km": round(road_distance, 2),
        "duration_minutes": travel_min,
        "source": "estimated",
    }


async def get_batch_travel_times(
    activities: list,
) -> dict:
    """Compute pairwise travel times for a list of activities.
    Returns dict: {(from_id, to_id): {"distance_km": ..., "duration_minutes": ...}}
    """
    result = {}
    for i, a in enumerate(activities):
        for j, b in enumerate(activities):
            if i == j:
                continue
            key = (a["id"], b["id"])
            if key not in result:
                info = await get_travel_info(
                    a["lat"], a["lng"], b["lat"], b["lng"]
                )
                result[key] = info
    return result
