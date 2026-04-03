"""Script to rewrite the tail of datasets.py"""
import os

filepath = os.path.join("backend", "models", "datasets.py")
data = open(filepath, "rb").read()
cut_point = data.find(b"_dynamic_city_cache")
head = data[:cut_point]

tail = b'''_dynamic_city_cache = {}

async def get_city_data(city: str) -> dict:
    """Get city data. Checks hardcoded, Indian cities, then AI fallback."""
    key = city.lower().strip()
    if key in CITY_DATA:
        return CITY_DATA[key]
    if key in _dynamic_city_cache:
        return _dynamic_city_cache[key]
    from .indian_cities import INDIAN_CITIES
    if key in INDIAN_CITIES:
        print(f"[DATASETS] Found \\'{key}\\' in Indian cities database")
        _dynamic_city_cache[key] = INDIAN_CITIES[key]
        return INDIAN_CITIES[key]
    for ik, iv in INDIAN_CITIES.items():
        if ik in key or key in ik or iv["name"].lower() == key:
            print(f"[DATASETS] Fuzzy matched \\'{key}\\' -> \\'{ik}\\'")
            _dynamic_city_cache[key] = iv
            return iv
    try:
        data = await generate_with_retry(
            f"Return ONLY valid JSON. Generate travel data for {city} with 16 attractions.",
            max_tokens=6000,
        )
        if data and "attractions" in data and len(data["attractions"]) > 0:
            for idx, att in enumerate(data["attractions"]):
                att.setdefault("id", f"gen_{key}_{idx:02d}")
                att["cost"] = float(att.get("cost", 0))
                att["duration_hours"] = float(att.get("duration_hours", 2.0))
                att["popularity"] = float(att.get("popularity", 0.8))
            _dynamic_city_cache[key] = data
            return data
    except Exception as e:
        print(f"[DATASETS] AI failed for {city}: {e}")
    print(f"[DATASETS] Using Goa fallback for \\'{key}\\'")
    fallback = INDIAN_CITIES.get("goa", CITY_DATA["nyc"])
    _dynamic_city_cache[key] = fallback
    return fallback


def get_available_cities() -> list:
    from .indian_cities import INDIAN_CITIES
    return list(CITY_DATA.keys()) + list(INDIAN_CITIES.keys()) + list(_dynamic_city_cache.keys())
'''

open(filepath, "wb").write(head + tail)
print(f"OK - wrote {len(head + tail)} bytes")
