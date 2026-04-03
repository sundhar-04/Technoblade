"""Script to finalize datasets.py to use local data"""
import os

filepath = os.path.join("backend", "models", "datasets.py")
data = open(filepath, "r", encoding="utf-8").read()
# Cut everything after CITY_DATA definition
cut_point = data.find("_dynamic_city_cache")
head = data[:cut_point]

tail = """_dynamic_city_cache = {}

async def get_city_data(city: str) -> dict:
    \"\"\"Get city data. Checks hardcoded international and Indian cities.\"\"\"
    key = city.lower().strip()
    if key in CITY_DATA:
        return CITY_DATA[key]
    if key in _dynamic_city_cache:
        return _dynamic_city_cache[key]
        
    from .indian_cities import INDIAN_CITIES
    if key in INDIAN_CITIES:
        print(f"[DATASETS] Found '{key}' in Indian cities database")
        _dynamic_city_cache[key] = INDIAN_CITIES[key]
        return INDIAN_CITIES[key]
        
    for ik, iv in INDIAN_CITIES.items():
        if ik in key or key in ik or iv["name"].lower() == key:
            print(f"[DATASETS] Fuzzy matched '{key}' -> '{ik}'")
            _dynamic_city_cache[key] = iv
            return iv
            
    # Fallback to Goa
    print(f"[DATASETS] Using Goa fallback for '{key}'")
    fallback = INDIAN_CITIES.get("goa", CITY_DATA.get("nyc", {}))
    _dynamic_city_cache[key] = fallback
    return fallback


def get_available_cities() -> list:
    from .indian_cities import INDIAN_CITIES
    return list(CITY_DATA.keys()) + list(INDIAN_CITIES.keys()) + list(_dynamic_city_cache.keys())
"""

# Also remove the import of generate_with_retry
head = head.replace("from ..routers.recommend import generate_with_retry\n", "")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(head + tail)
print("datasets.py finalized without HF dependency!")
