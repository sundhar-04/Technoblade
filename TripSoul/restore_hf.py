"""Script to finalize datasets.py to use HF API with correct limits"""
import os

filepath = os.path.join("backend", "models", "datasets.py")
data = open(filepath, "r", encoding="utf-8").read()
# Cut everything after CITY_DATA definition
cut_point = data.find("_dynamic_city_cache")
head = data[:cut_point]

tail = """_dynamic_city_cache = {}

async def get_city_data(city: str) -> dict:
    \"\"\"Get city data. Checks hardcoded international cities, then generates via HF AI.\"\"\"
    key = city.lower().strip()
    
    if key in CITY_DATA:
        return CITY_DATA[key]
    if key in _dynamic_city_cache:
        return _dynamic_city_cache[key]
        
    print(f"[DATASETS] City '{key}' not in hardcoded DB. Generating via AI...")
    
    from ..routers.recommend import generate_with_retry
    
    prompt = f\"\"\"Return ONLY valid JSON. No markdown.
    Generate a highly realistic and curated travel dataset for the city: {city}.
    Include exactly 8 distinct attractions covering different categories (history, nature, culture, shopping, adventure, food, nightlife).
    Prices should be in local currency equivalent but normalized roughly to USD amounts logically (e.g. 5.0 to 100.0). Keep strings clean.

    {{
      "name": "{city.title()}",
      "country": "India (or appropriate country)",
      "timezone": "Asia/Kolkata",
      "center": {{"lat": 15.2993, "lng": 74.1240}},
      "currency": "INR",
      "attractions": [
        {{
          "id": "gen_{key}_01",
          "name": "Iconic Landmark Name",
          "category": "culture",
          "lat": 15.3000,
          "lng": 74.1250,
          "cost": 10.0,
          "duration_hours": 2.0,
          "popularity": 0.95,
          "description": "Evocative one sentence description.",
          "weather_sensitive": false,
          "opening_hour": 9,
          "closing_hour": 18
        }}
      ]
    }}
    Provide exactly 8 attractions in the "attractions" array. Use real-world rough coordinates.
    \"\"\"
    
    try:
        # User reported max tokens limit exceeded. Limit set to 3000 to fit well within 4096.
        data = await generate_with_retry(prompt, max_tokens=3000)
        
        if data and "attractions" in data and len(data["attractions"]) > 0:
            # Standardize missing fields
            for idx, att in enumerate(data["attractions"]):
                att["id"] = att.get("id", f"gen_{key}_{idx:02d}")
                att["category"] = att.get("category", "culture")
                att["cost"] = float(att.get("cost", 0.0))
                att["duration_hours"] = float(att.get("duration_hours", 2.0))
                att["popularity"] = float(att.get("popularity", 0.8))
                att["weather_sensitive"] = bool(att.get("weather_sensitive", False))
                att["opening_hour"] = int(att.get("opening_hour", 9))
                att["closing_hour"] = int(att.get("closing_hour", 18))
                
            _dynamic_city_cache[key] = data
            return data
    except Exception as e:
        print(f"[DATASETS] AI Generation failed for {city}: {e}")
        
    print(f"[DATASETS] Falling back to NYC for {city}.")
    return CITY_DATA["nyc"]


def get_available_cities() -> list:
    \"\"\"Return list of available city keys.\"\"\"
    return list(CITY_DATA.keys()) + list(_dynamic_city_cache.keys())
"""

if "generate_with_retry" not in head:
    # We must add the import back to the top just after asyncio
    head = head.replace("import asyncio\n", "import asyncio\nfrom ..routers.recommend import generate_with_retry\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(head + tail)
print("datasets.py restored to HF generation securely.")
