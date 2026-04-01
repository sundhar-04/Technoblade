import os
import re
import json
import hashlib
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# ─────────────────────────────────────────
# Setup
# ─────────────────────────────────────────
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

hf_client = InferenceClient(
    model="Qwen/Qwen3-8B",
    token=HF_TOKEN,
    timeout=60,
)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {}


# ─────────────────────────────────────────
# Schema
# ─────────────────────────────────────────
class TripSoulPreferences(BaseModel):
    mood:     List[str]
    who:      List[str]
    pace:     List[str]
    style:    List[str]
    duration: List[str]
    scenery:  List[str]
    food:     List[str]
    season:   List[str]
    region:   List[str]
    notes:    Optional[str]       = ""
    exclude:  Optional[List[str]] = []


# ─────────────────────────────────────────
# HF Generator — strips <think> blocks
# ─────────────────────────────────────────
async def generate_with_hf(prompt: str):
    cache_key = hashlib.md5(prompt.encode()).hexdigest()

    if cache_key in _cache:
        print("[CACHE HIT]")
        return _cache[cache_key]

    try:
        response = hf_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.7,
        )

        output = response.choices[0].message.content

        if not output:
            print("[HF ERROR] Empty response")
            return None

        print("[RAW]", output[:300])

        # ── KEY FIX: strip <think>...</think> block that Qwen3 emits ──
        text = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()

        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?\s*", "", text).strip()
        text = re.sub(r"```\s*$", "", text).strip()

        print("[CLEANED]", text[:300])

        parsed = json.loads(text)
        _cache[cache_key] = parsed
        return parsed

    except json.JSONDecodeError as e:
        print("[JSON ERROR]", str(e))
        print("[TEXT WAS]", text[:500] if 'text' in dir() else "unavailable")
        return None
    except Exception as e:
        print("[HF ERROR]", str(e))
        return None


# ─────────────────────────────────────────
# Root
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "TripSoul HF Backend Online"}


# ─────────────────────────────────────────
# /recommend
# ─────────────────────────────────────────
@app.post("/recommend")
async def recommend(prefs: TripSoulPreferences):
    style    = prefs.style[0] if prefs.style else "Comfortable"
    excluded = ", ".join(prefs.exclude) if prefs.exclude else "None"

    print(f"\n====== /recommend called ======")
    print(f"exclude: {prefs.exclude}")
    print(f"mood: {prefs.mood}, region: {prefs.region}, style: {style}")

    prompt = f"""You are TripSoul, an emotionally intelligent Indian travel guide.

TASK: Recommend exactly 3 Indian travel destinations that match this traveller profile.

Region: {', '.join(prefs.region) or 'Anywhere'}
Mood: {', '.join(prefs.mood) or 'Not specified'}
Travel style: {style}
Season: {', '.join(prefs.season) or 'Any'}
Scenery: {', '.join(prefs.scenery) or 'Any'}
Companions: {', '.join(prefs.who) or 'Not specified'}
Pace: {', '.join(prefs.pace) or 'Not specified'}
Food: {', '.join(prefs.food) or 'Not specified'}
Notes: {prefs.notes or 'None'}
EXCLUDED (do not suggest these): {excluded}

STRICT RULES:
- Return ONLY a valid JSON object, nothing else.
- No explanation, no markdown, no code fences.
- Do not include <think> or any reasoning. Output JSON directly.

OUTPUT FORMAT (follow exactly):
{{
  "recommendations": [
    {{
      "name": "Place name",
      "state": "State name",
      "icon": "🌄",
      "reason": "Exactly 2 sentences, evocative and personal, referencing mood and companions.",
      "itinerary_hint": "2 practical lines including at least one ₹ price and one landmark.",
      "tags": ["Tag1", "Tag2", "Tag3"]
    }}
  ]
}}"""

    data = await generate_with_hf(prompt)

    if data and "recommendations" in data:
        # Sanitise each recommendation
        for rec in data["recommendations"]:
            rec["tags"] = rec.get("tags", [])[:3]
            while len(rec["tags"]) < 3:
                rec["tags"].append("India")
            words = rec.get("reason", "").split()
            if len(words) > 50:
                rec["reason"] = " ".join(words[:50]) + "..."
            if not rec.get("icon"):
                rec["icon"] = "📍"

        print(f"[SUCCESS] {len(data['recommendations'])} recommendations returned")
        return data

    # Fallback
    print("!!! FALLBACK TRIGGERED !!!")
    return {
        "recommendations": [
            {
                "name": "Manali",
                "state": "Himachal Pradesh",
                "icon": "🏔️",
                "reason": "Snow-capped peaks and pine forests make Manali a year-round escape. Old Manali's cafes and the Solang Valley slopes suit every pace.",
                "itinerary_hint": "Guesthouse in Old Manali (₹700/night). Trek to Jogini Falls at dawn, snow activities at Solang Valley.",
                "tags": ["Mountains", "Snow", "Adventure"]
            },
            {
                "name": "Rishikesh",
                "state": "Uttarakhand",
                "icon": "🧘",
                "reason": "Spirituality meets high-energy adventure where the Ganga roars through the valley. Sunrise yoga on the ghats resets even the most restless soul.",
                "itinerary_hint": "Ashram stay (₹500/night). Whitewater raft at 7am, attend Parmarth Niketan Ganga Aarti at 6pm.",
                "tags": ["Yoga", "River", "Adventure"]
            },
            {
                "name": "Hampi",
                "state": "Karnataka",
                "icon": "🏛️",
                "reason": "Ancient Vijayanagara ruins sprawl across a surreal boulder landscape unlike anywhere else in India. Cycling between temples at golden hour is pure magic.",
                "itinerary_hint": "Guesthouse near Virupaksha (₹600/night). Cycle the ruins at sunrise, coracle ride at Tungabhadra in the evening.",
                "tags": ["Ruins", "Heritage", "Cycling"]
            }
        ]
    }


# ─────────────────────────────────────────
# /handbook/{city}
# ─────────────────────────────────────────
_handbook_cache: dict = {}

@app.get("/handbook/{city}")
async def get_handbook(city: str):
    city_key = city.lower().strip()

    if city_key in _handbook_cache:
        print(f"[CACHE HIT] Handbook for {city}")
        return _handbook_cache[city_key]

    prompt = f"""You are TripSoul's lead destination researcher.
Generate a travel handbook for {city}, India.

Return ONLY valid JSON. No markdown, no explanation, no <think> tags.

{{
  "city": "{city}",
  "state": "State name",
  "tagline": "Poetic tagline for {city}",
  "best_time": "Best months to visit with reasoning",
  "safety_score": 8,
  "safety_note": "One sentence safety summary",
  "aqi": {{ "value": 55, "season": "Winter", "advisory": "Air quality advice" }},
  "connectivity": {{ "flight": "Nearest airport info", "train": "Train connectivity", "road": "Road access" }},
  "budget_per_day": {{ "backpacker": "₹800–₹1,200", "comfortable": "₹2,500–₹4,500", "luxury": "₹8,000+" }},
  "must_try_food": ["Dish 1", "Dish 2", "Dish 3"],
  "fine_dining": ["Restaurant 1 — signature dish", "Restaurant 2 — signature dish"],
  "cafes": ["Cafe 1", "Cafe 2"],
  "hidden_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "avoid": "One sentence on what to watch out for",
  "top_experiences": [
    {{ "name": "Experience name", "cost": "₹XXX", "duration": "2 hours" }}
  ],
  "nearby_day_trips": ["Place 1 (45 km)", "Place 2 (60 km)"]
}}"""

    data = await generate_with_hf(prompt)

    if data:
        _handbook_cache[city_key] = data
        return data

    # Fallback
    print(f"!!! HANDBOOK FALLBACK for {city} !!!")
    return {
        "city": city,
        "state": "India",
        "tagline": f"Discover the soul of {city}",
        "best_time": "October to March",
        "safety_score": 7,
        "safety_note": "Generally safe. Stay alert in crowded areas.",
        "aqi": {"value": 50, "season": "Current", "advisory": "Moderate air quality."},
        "connectivity": {"flight": "Check nearest airport", "train": "Check IRCTC", "road": "Well connected by highway"},
        "budget_per_day": {"backpacker": "₹800–₹1,200", "comfortable": "₹2,000–₹3,500", "luxury": "₹6,000+"},
        "must_try_food": ["Local thali", "Street chaat", "Regional speciality"],
        "fine_dining": ["Check local listings"],
        "cafes": ["Explore local markets"],
        "hidden_tips": ["Ask locals for seasonal tips", "Visit early morning to avoid crowds"],
        "avoid": "Avoid peak holiday weekends if you prefer a quieter experience.",
        "top_experiences": [{"name": "Local sightseeing", "duration": "Half day", "cost": "₹200–₹500"}],
        "nearby_day_trips": ["Explore surrounding villages"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)