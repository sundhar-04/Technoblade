"""
Recommend Router — AI-powered destination recommendations and handbooks.
Ported from pr_05 branch's main.py into modular backend architecture.
Uses HuggingFace Qwen model for intelligent travel suggestions.
"""
import os
import re
import json
import asyncio
import hashlib
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/recommend", tags=["recommend"])

# ─── HuggingFace setup ───
HF_TOKEN = os.getenv("HF_TOKEN")
_hf_client = None
_hf_checked = False

def _get_hf_client():
    global _hf_client
    if _hf_client is None and HF_TOKEN:
        try:
            from huggingface_hub import AsyncInferenceClient
            _hf_client = AsyncInferenceClient(
                model="Qwen/Qwen2.5-7B-Instruct",
                token=HF_TOKEN,
                timeout=60,
            )
        except Exception as e:
            print(f"[RECOMMEND] HF client init failed: {e}")
    return _hf_client


_cache: dict = {}
_handbook_cache: dict = {}


# ─── Schema ───
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

    @field_validator(
        'mood', 'who', 'pace', 'style',
        'duration', 'scenery', 'food', 'season', 'region',
        mode='before'
    )
    @classmethod
    def default_empty_list(cls, v):
        return v if v else []


# ─── Helpers ───
def clean_json_string(raw_text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx == -1 or end_idx == -1:
        return text
    return text[start_idx:end_idx + 1]


async def generate_with_retry(prompt: str, retries: int = 3, delay: int = 2, max_tokens: int = 2000) -> Optional[dict]:
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    if cache_key in _cache:
        print("[CACHE HIT] Returning cached response")
        return _cache[cache_key]

    client = _get_hf_client()
    if not client:
        print("[RECOMMEND] No HF client available — using fallback")
        return None

    for attempt in range(retries):
        try:
            print(f"\n--- HF model attempt {attempt + 1} ---")
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            raw = response.choices[0].message.content
            if not raw:
                print("[HF ERROR] Empty response")
                continue

            print(f"[RAW] {raw[:300]}")
            json_text = clean_json_string(raw)
            if not json_text or '{' not in json_text:
                print("[NO JSON FOUND] - triggering retry")
                continue

            parsed = json.loads(json_text)
            print(f"[PARSED OK] keys={list(parsed.keys())}")
            _cache[cache_key] = parsed
            return parsed

        except json.JSONDecodeError as e:
            err_msg = f"[JSON ERROR] {e} - RAW TEXT: {raw[:300]}"
            print(err_msg)
            with open("hf_error.txt", "a", encoding="utf-8") as err_log:
                err_log.write(err_msg + "\n")
            continue
        except Exception as e:
            err_msg = f"[ERROR] {type(e).__name__}: {str(e)[:200]}"
            print(err_msg)
            with open("hf_error.txt", "a", encoding="utf-8") as err_log:
                err_log.write(err_msg + "\n")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (attempt + 1))
            else:
                break

    print("[ALL ATTEMPTS FAILED] Using fallback")
    return None


# ─── Endpoints ───
@router.post("/destinations")
async def get_recommendations(prefs: TripSoulPreferences):
    """AI-powered destination recommendations based on user preferences."""
    style    = prefs.style[0] if prefs.style else "Comfortable"
    excluded = ", ".join(prefs.exclude) if prefs.exclude else "None"

    print(f"\n====== /recommend/destinations called ======")
    print(f"exclude: {prefs.exclude}")
    print(f"mood: {prefs.mood}, region: {prefs.region}, style: {style}")

    prompt = f"""You are TripSoul, an emotionally intelligent Indian travel guide. \
You write with warmth, specificity, and cultural depth.

ABSOLUTE CONSTRAINT: The following places are banned: {excluded}.

TASK: Recommend exactly 3 Indian travel destinations matching this traveller:

1. Region: {', '.join(prefs.region) or 'Anywhere in India'}
2. Season: {', '.join(prefs.season) or 'Any season'}
3. Mood: {', '.join(prefs.mood) or 'Not specified'}
4. Scenery: {', '.join(prefs.scenery) or 'Not specified'}
5. Travel style: {style}
6. Duration: {', '.join(prefs.duration) or 'Flexible'}
7. Companions: {', '.join(prefs.who) or 'Not specified'}
8. Pace: {', '.join(prefs.pace) or 'Not specified'}
9. Food: {', '.join(prefs.food) or 'Not specified'}
10. Notes: {prefs.notes or 'None'}

RULES:
- "reason": Exactly 2 sentences, max 40 words. Evocative and personal.
- "itinerary_hint": 2 lines with at least one ₹ price and one named landmark.
- "tags": exactly 3, specific.

Return ONLY valid JSON. No markdown. No explanation.

OUTPUT:
{{
  "recommendations": [
    {{
      "name": "City name",
      "state": "State name",
      "icon": "🏔️",
      "reason": "2-sentence evocative reason",
      "itinerary_hint": "2-line practical plan",
      "tags": ["Tag1", "Tag2", "Tag3"]
    }}
  ]
}}"""

    data = await generate_with_retry(prompt)
    if data and "recommendations" in data:
        for rec in data["recommendations"]:
            rec["tags"] = rec.get("tags", [])[:3]
            while len(rec["tags"]) < 3:
                rec["tags"].append("India")
            words = rec.get("reason", "").split()
            if len(words) > 45:
                rec["reason"] = " ".join(words[:45]) + "..."
            if not rec.get("icon"):
                rec["icon"] = "📍"

        recs = data.get("recommendations", [])
        if len(recs) < 3:
            fallback = [
                {"name": "Kasol", "state": "Himachal Pradesh", "icon": "🌲",
                 "reason": "A peaceful riverside retreat perfect for quiet bonding.",
                 "itinerary_hint": "Stay ₹600. Walk Parvati river trail.",
                 "tags": ["Chill", "Nature", "River"]},
                {"name": "McLeod Ganj", "state": "Himachal Pradesh", "icon": "🏔️",
                 "reason": "A calm hill town blending Tibetan culture and mountain serenity.",
                 "itinerary_hint": "Hostel ₹500. Visit Dalai Lama temple.",
                 "tags": ["Culture", "Mountains", "Peace"]}
            ]
            data["recommendations"] += fallback
        data["recommendations"] = data["recommendations"][:3]

        print(f"[SUCCESS] {len(data['recommendations'])} recommendations")
        return data

    # Fallback
    print("!!! FALLBACK TRIGGERED !!!")
    return {
        "recommendations": [
            {"name": "Manali", "state": "Himachal Pradesh", "icon": "🏔️",
             "reason": "Snow-capped peaks and pine forests make Manali a year-round escape. Old Manali's cafes and Solang Valley slopes suit every pace.",
             "itinerary_hint": "Guesthouse in Old Manali (₹700/night). Trek to Jogini Falls at dawn, snow activities at Solang Valley.",
             "tags": ["Mountains", "Snow", "Adventure"]},
            {"name": "Rishikesh", "state": "Uttarakhand", "icon": "🧘",
             "reason": "Spirituality meets high-energy adventure where the Ganga roars through the valley. Sunrise yoga on the ghats resets even the most restless soul.",
             "itinerary_hint": "Ashram stay (₹500/night). Whitewater raft at 7am, attend Parmarth Niketan Ganga Aarti at 6pm.",
             "tags": ["Yoga", "River", "Adventure"]},
            {"name": "Hampi", "state": "Karnataka", "icon": "🏛️",
             "reason": "Ancient Vijayanagara ruins sprawl across a surreal boulder landscape unlike anywhere else in India. Cycling between temples at golden hour is pure magic.",
             "itinerary_hint": "Guesthouse near Virupaksha (₹600/night). Cycle the ruins at sunrise, coracle ride at Tungabhadra in the evening.",
             "tags": ["Ruins", "Heritage", "Cycling"]}
        ]
    }


@router.get("/handbook/{city}")
async def get_handbook(city: str):
    """Generate a detailed travel handbook for a given city using AI."""
    city_key = city.lower().strip()

    if city_key in _handbook_cache:
        print(f"[CACHE HIT] Handbook for {city}")
        return _handbook_cache[city_key]

    prompt = f"""Return ONLY valid JSON. No markdown, no prose.
You are TripSoul's lead destination researcher.
Generate a hyper-detailed travel handbook for {city}, India.

{{
  "city": "{city}",
  "state": "State name",
  "tagline": "Evocative tagline",
  "best_time": "Best months with reasoning",
  "safety_score": 8,
  "safety_note": "One sentence safety summary",
  "aqi": {{ "value": 55, "season": "Winter", "advisory": "Air quality advice" }},
  "connectivity": {{ "flight": "Nearest airport info", "train": "Train connectivity", "road": "Road access" }},
  "budget_per_day": {{ "backpacker": "₹800–₹1,200", "comfortable": "₹2,500–₹4,500", "luxury": "₹8,000+" }},
  "must_try_food": ["Dish 1", "Dish 2", "Dish 3"],
  "fine_dining": ["Restaurant 1 — signature dish"],
  "cafes": ["Cafe 1", "Cafe 2"],
  "hidden_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "avoid": "One sentence on what to watch out for",
  "top_experiences": [
    {{ "name": "Experience name", "cost": "₹XXX", "duration": "2 hours" }}
  ],
  "nearby_day_trips": ["Place 1 (45 km)", "Place 2 (60 km)"]
}}"""

    data = await generate_with_retry(prompt, max_tokens=4000)

    if data:
        _handbook_cache[city_key] = data
        return data

    print(f"!!! HANDBOOK FALLBACK for {city} !!!")
    return {
        "city": city,
        "state": "India",
        "tagline": f"Discover the soul of {city}",
        "best_time": "October to March",
        "safety_score": 7,
        "safety_note": "Generally safe for travellers. Stay alert in crowded areas.",
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
