import os
import re
import json
import asyncio
import hashlib
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = InferenceClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    token=HF_TOKEN,
    timeout=60,
)

# ─────────────────────────────────────────────
# DEV MODE: Set True while tweaking UI.
# No API calls will be made — fallback fires instantly.
DEV_MODE = False
# ─────────────────────────────────────────────

_cache: dict = {}
_handbook_cache: dict = {}

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


def clean_json_string(raw_text: str) -> str:
    # Remove thought blocks
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    # Find the first '{' and the last '}'
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    if start_idx == -1 or end_idx == -1:
        return text
    return text[start_idx:end_idx + 1]

async def generate_with_retry(prompt: str, retries: int = 3, delay: int = 2, max_tokens: int = 2000) -> Optional[dict]:
    # ── Cache check ──────────────────────────────────────────────────────────
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    if cache_key in _cache:
        print("[CACHE HIT] Returning cached response — no API call made")
        return _cache[cache_key]

    # ── Dev mode short-circuit ───────────────────────────────────────────────
    if DEV_MODE:
        print("[DEV MODE] Skipping API call — returning None to trigger fallback")
        return None

    for attempt in range(retries):
        try:
            print(f"\n--- Trying Hugging Face model (attempt {attempt + 1}) ---")
            response = hf_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            raw = response.choices[0].message.content
            if not raw:
                print("[HF ERROR] Empty response")
                continue
                
            print(f"[RAW]\n{raw[:300]}\n")

            json_text = clean_json_string(raw)
            if not json_text or '{' not in json_text:
                print("[NO JSON FOUND] - triggering retry")
                continue

            parsed = json.loads(json_text)
            print(f"[PARSED OK] keys={list(parsed.keys())}")

            _cache[cache_key] = parsed
            print(f"[CACHED] Response stored for future identical requests")
            return parsed

        except json.JSONDecodeError as e:
            print(f"[JSON ERROR] {e}")
            break

        except Exception as e:
            err = str(e)
            print(f"[ERROR] {type(e).__name__}: {err[:200]}")
            if attempt < retries - 1:
                await asyncio.sleep(delay * (attempt + 1))
            else:
                break

    print("[ALL MODELS FAILED] Using fallback")
    return None


@app.get("/")
def root():
    return {"status": "TripSoul Online", "api": "v4.0-multi-model"}


@app.post("/recommend")
async def get_recommendations(prefs: TripSoulPreferences):
    style    = prefs.style[0] if prefs.style else "Comfortable"
    excluded = ", ".join(prefs.exclude) if prefs.exclude else "None"

    print(f"\n====== /recommend called ======")
    print(f"exclude: {prefs.exclude}")
    print(f"mood: {prefs.mood}, region: {prefs.region}, style: {style}")

    prompt = f"""You are TripSoul, an emotionally intelligent Indian travel guide. \
You write with warmth, specificity, and cultural depth. You never suggest generic tourist clichés.

ABSOLUTE CONSTRAINT: The following places are banned from your response: {excluded}.
If the list is empty, ignore this line.

TASK: Recommend exactly 3 Indian travel destinations that match the traveller profile below.

PRIORITY ORDER (match in this sequence — top = most important):
1. Region: {', '.join(prefs.region) or 'Anywhere in India'}
2. Season: {', '.join(prefs.season) or 'Any season'}
3. Mood: {', '.join(prefs.mood) or 'Not specified'}
4. Scenery: {', '.join(prefs.scenery) or 'Not specified'}
5. Travel style: {style} (shapes budget and lodging in itinerary_hint)
6. Duration: {', '.join(prefs.duration) or 'Flexible'}
7. Companions: {', '.join(prefs.who) or 'Not specified'}
8. Pace: {', '.join(prefs.pace) or 'Not specified'}
9. Food: {', '.join(prefs.food) or 'Not specified'}
10. Notes: {prefs.notes or 'None'}

TONE RULES:
- "reason": Exactly 2 sentences, maximum 40 words total. Evocative and personal — reference their mood and companions directly.
  Do NOT use generic phrases like "perfect destination" or "ideal for travellers".
- "itinerary_hint": 2 lines. Must include at least one specific price in ₹ and one named trail, dish, or landmark.
- "tags": exactly 3. Specific over generic — prefer "Living root bridges" over "Nature".

EXAMPLE of a high-quality entry (do not copy this — it's only to show format and depth):
{{
  "name": "Dzükou Valley",
  "state": "Nagaland",
  "icon": "🌿",
  "reason": "For two friends chasing stillness, Dzükou offers a silence so complete you can hear the grass grow. The valley blooms in July like a secret only the prepared ever find.",
  "itinerary_hint": "Budget camp at the valley base (₹300/night). Trek the 4-hour ridge trail at dawn for the full lily bloom.",
  "tags": ["Lily valley", "Ridge trek", "Off-grid"]
}}

Return ONLY a valid JSON object. No markdown. No explanation. No code fences.
You MUST return exactly 3 recommendations. (min_items: 3)

OUTPUT STRUCTURE:
{{
  "recommendations": [
    {{
      "name": "City or place name",
      "state": "State name",
      "icon": "Single emoji",
      "reason": "2-sentence evocative reason referencing their mood and companions",
      "itinerary_hint": "2-line practical plan for {style} traveller",
      "tags": ["Tag1", "Tag2", "Tag3"]
    }}
  ]
}}"""

    data = await generate_with_retry(prompt)
    if data and "recommendations" in data:
        # Sanitise tags, reason, and icon for EVERY recommendation
        for rec in data["recommendations"]:
            # 1. Ensure exactly 3 tags
            rec["tags"] = rec.get("tags", [])[:3]
            while len(rec["tags"]) < 3:
                rec["tags"].append("India")

            # 2. Truncate reason if it exceeds 45 words
            words = rec.get("reason", "").split()
            if len(words) > 45:
                rec["reason"] = " ".join(words[:45]) + "..."

            # 3. Ensure a fallback icon exists
            if not rec.get("icon"):
                rec["icon"] = "📍"

        recs = data.get("recommendations", [])

        if len(recs) < 3:
            print("[FIX] Not enough recommendations, using fallback to fill")

            fallback = [
                {
                    "name": "Kasol",
                    "state": "Himachal Pradesh",
                    "icon": "🌲",
                    "reason": "A peaceful riverside retreat perfect for quiet bonding.",
                    "itinerary_hint": "Stay ₹600. Walk Parvati river trail.",
                    "tags": ["Chill", "Nature", "River"]
                },
                {
                    "name": "McLeod Ganj",
                    "state": "Himachal Pradesh",
                    "icon": "🏔️",
                    "reason": "A calm hill town blending Tibetan culture and mountain serenity.",
                    "itinerary_hint": "Hostel ₹500. Visit Dalai Lama temple.",
                    "tags": ["Culture", "Mountains", "Peace"]
                }
            ]

            data["recommendations"] += fallback

        # ensure exactly 3
        data["recommendations"] = data["recommendations"][:3]

        print(f"[SUCCESS] {len(data['recommendations'])} recommendations")
        return data

    # Fallback only runs if data is None or missing key
    print("!!! FALLBACK TRIGGERED !!!")
    return {
        "recommendations": [
            { "name": "Manali", "state": "Himachal Pradesh", "icon": "🏔️", "reason": "A perfect mountain escape matching your vibe.", "itinerary_hint": "Stay in Old Manali (₹800/night). Trek to Jogini Falls at dawn.", "tags": ["Mountains", "Classic", "Scenic"] },
            { "name": "Rishikesh", "state": "Uttarakhand", "icon": "🧘", "reason": "Spirituality meets high-energy adventure on the Ganga.", "itinerary_hint": "Ashram stay (₹500/night). River raft at 7am, Ganga Aarti at 6pm.", "tags": ["Yoga", "Adventure", "River"] },
            { "name": "Kasol", "state": "Himachal Pradesh", "icon": "🌲", "reason": "The ultimate chill destination for nature lovers.", "itinerary_hint": "Guesthouse in the village (₹600/night). Trek to Kheerganga hot springs.", "tags": ["Forests", "Chill", "Trek"] }
        ]
    }


@app.get("/handbook/{city}")
async def get_handbook(city: str):
    city_key = city.lower().strip()

    # 1. Check Cache
    if city_key in _handbook_cache:
        print(f"[CACHE HIT] Handbook for {city}")
        return _handbook_cache[city_key]

    # 2. Prepare Prompt
    prompt = f"""Return ONLY valid JSON. No markdown, no prose.
You are TripSoul's lead destination researcher. 
Generate a hyper-detailed, authoritative travel handbook for {city}, India.

{{
  "city": "{city}",
  "state": "State name",
  "tagline": "Evocative tagline",
  "Overview": {{
    "destination_name": "{city}, State",
    "tagline": "Extended description",
    "hero_images": [
      {{ "scene": "Iconic landmark", "mood": "Cinematic", "time_of_day": "Golden Hour" }}
    ]
  }},
  "real_time": {{
    "aqi": {{ "avg_aqi": 55, "season": "Current", "advisory": "Expert air quality advice" }},
    "best_time_to_visit": "Months with reasoning",
    "seasonal_breakdown": [
      {{ "season": "Summer", "conditions": "Temp/Weather info", "crowd_level": "High" }}
    ],
    "traffic_tips": ["Commuting peaks"],
    "festivals": [{{ "name": "Festival", "month": "Month", "description": "Why it matters" }}]
  }},
  "budget": {{
    "Backpacker": "₹800–₹1,500",
    "Comfortable": "₹2,500–₹5,000",
    "Luxury": "₹10,000+"
  }},
  "connectivity": [
    {{ "mode": "Flight", "details": "Nearest airport", "booking_tip": "When to book" }}
  ],
  "things_to_do": [
    {{ "traveler_type": "Adventure", "activities": ["Specific trek name", "Specific activity"] }}
  ],
  "food": {{
    "must_try_dishes": ["Dish Name (Description)"],
    "fine_dining": ["Restaurant Name - What to order"],
    "cafe_picks": ["Hidden gem cafe names"],
    "hygiene_tips": ["Street food safety advice"]
  }},
  "culture": {{
    "historical_context": "Deep-dive 2-sentence history",
    "spiritual_sites": ["Site Name - Significance"],
    "shopping_crafts": ["What to buy & market"],
    "unesco_sites": [{{ "name": "Site", "status": "UNESCO/Notable", "note": "Tip" }}]
  }},
  "offbeat_gems": [
    {{ "name": "Place", "why_special": "Why tourists miss it", "best_for": "Photography", "distance_from_town": "Distance" }}
  ],
  "safety": {{
    "safety_score": 9,
    "general_tips": ["Night safety"],
    "womens_safety": ["Specific advice for solo women"],
    "emergency_contacts": {{ "police": "100", "ambulance": "102" }},
    "accessibility_sites": [
      {{ "site": "Landmark", "wheelchair": true, "steps_involved": "0", "mobility_notes": "Ramp info" }}
    ]
  }},
  "practicalities": {{
    "permits": ["Inner Line Permit info if applicable"],
    "currency_tips": ["ATM & UPI"],
    "network_coverage": "Reliability",
    "health_hygiene": ["Water safety"]
  }},
  "Day_Trips": [
    {{ "name": "Excursion", "highlights": "What to see", "distance_km": 45, "duration": "Full Day" }}
  ],
  "Responsible_Travel": {{
    "cultural_etiquette": ["Dress codes"],
    "sustainability_tips": ["Water conservation"],
    "support_local": ["NGO or artisan collective"]
  }},
  "Media_Hub": {{
    "photography_spots": ["Exact spot for sunrise view"]
  }}
}}"""

    # 3. Call AI with your existing retry logic
    data = await generate_with_retry(prompt, max_tokens=4000)

    if data:
        _handbook_cache[city_key] = data
        return data

    # 4. Fallback (If AI fails or DEV_MODE is True)
    print(f"!!! HANDBOOK FALLBACK TRIGGERED for {city} !!!")
    return {
        "city": city,
        "state": "India",
        "tagline": f"Discover the soul of {city}",
        "best_time": "October to March",
        "safety_score": 7,
        "safety_note": "Generally safe for travellers. Stay alert in crowded areas.",
        "connectivity": "Check IRCTC for trains and local bus services.",
        "budget_per_day": { "backpacker": "₹800–₹1200", "comfortable": "₹2000–₹3500", "luxury": "₹6000+" },
        "must_try_food": ["Local thali", "Street chaat", "Regional speciality"],
        "fine_dining": ["Check local listings"],
        "cafes": ["Explore local markets for hidden gems"],
        "hidden_tips": ["Ask locals for seasonal recommendations", "Visit early morning to avoid crowds"],
        "avoid": "Avoid peak holiday weekends if you prefer a quieter experience.",
        "top_experiences": [{ "name": "Local sightseeing", "duration": "Half day", "cost": "₹200–₹500" }],
        "accessibility": { "wheelchair": False, "notes": "Terrain varies — check specific sites in advance." },
        "aqi": { "value": 50, "season": "Current", "advisory": "Moderate air quality." },
        "nearby_day_trips": ["Explore the surrounding rural landscape"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)