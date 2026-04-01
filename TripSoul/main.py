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
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

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


async def generate_with_retry(prompt: str, retries: int = 3, delay: int = 2):
    # ── Cache check ──────────────────────────────────────────────────────────
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    if cache_key in _cache:
        print("[CACHE HIT] Returning cached response — no API call made")
        return _cache[cache_key]

    # ── Dev mode short-circuit ───────────────────────────────────────────────
    if DEV_MODE:
        print("[DEV MODE] Skipping API call — returning None to trigger fallback")
        return None

    # ── Model list: most stable first ───────────────────────────────────────
    # gemini-1.5-flash is tried first as it has the widest availability.
    # Bump a model to the top if you find it works better for your key/region.
    models = [
    "gemini-2.5-flash",      # Current stable — try first
    "gemini-2.0-flash",      # Keep as fallback until you confirm 2.5 works
]

    for model in models:
        for attempt in range(retries):
            try:
                print(f"\n--- Trying {model} (attempt {attempt + 1}) ---")
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                raw = response.text.strip()
                print(f"[RAW]\n{raw[:300]}\n")

                text = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE).strip()
                text = re.sub(r"```\s*$", "", text).strip()

                parsed = json.loads(text)
                print(f"[PARSED OK] model={model} keys={list(parsed.keys())}")

                # Store in cache before returning
                _cache[cache_key] = parsed
                print(f"[CACHED] Response stored for future identical requests")
                return parsed

            except json.JSONDecodeError as e:
                print(f"[JSON ERROR] {e}")
                break  # Bad JSON from this model — try next model, not retry

            except Exception as e:
                err = str(e)
                print(f"[ERROR] {type(e).__name__}: {err[:200]}")

                if "404" in err or "NOT_FOUND" in err:
                    print(f"[SKIP] {model} not available, trying next model...")
                    break  # Model doesn't exist for this key/region — skip immediately

                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    match = re.search(r"retry in ([\d.]+)s", err)
                    # Use Google's suggested wait if provided, otherwise 30s minimum
                    wait = max(float(match.group(1)) + 2, 30) if match else 30
                    print(f"[RATE LIMIT] Quota hit on {model}. Waiting {wait}s...")
                    if attempt < retries - 1:
                        await asyncio.sleep(wait)
                    else:
                        print(f"[RATE LIMIT] All retries exhausted for {model}, trying next model...")
                        break

                elif attempt < retries - 1:
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
    prompt = f"""
    Return ONLY valid JSON.
No markdown, no explanation.

Rules:
- Use double quotes only
- No trailing commas
- Escape all quotes inside text
- Ensure JSON is complete and valid
    You are TripSoul's lead destination researcher. 
Generate a hyper-detailed, authoritative travel handbook for {city}, India.
This data will power a dedicated destination page; ensure information is granular and expert-level.

Return ONLY a valid JSON object. No markdown, no prose.

{{
  "city": "{city}",
  "state": "State name",
  "tagline": "A poetic, evocative tagline specific to {city}'s soul",
  "Overview": {{
    "destination_name": "{city}, State",
    "tagline": "Extended evocative description",
    "hero_images": [
      {{ "scene": "Iconic landmark", "mood": "Cinematic", "time_of_day": "Golden Hour" }},
      {{ "scene": "Local street life", "mood": "Vibrant", "time_of_day": "Noon" }}
    ]
  }},
  "Real_Time_Content": {{
    "aqi": {{ "avg_aqi": 55, "season": "Current", "advisory": "Expert air quality advice" }},
    "best_time_to_visit": "Months with specific weather/festival reasoning",
    "seasonal_breakdown": [
      {{ "season": "Summer", "conditions": "Temp/Weather info", "crowd_level": "High/Medium/Low" }},
      {{ "season": "Monsoon", "conditions": "Temp/Weather info", "crowd_level": "Low" }}
    ],
    "traffic_tips": ["Expert advice on local commuting peaks"],
    "festivals": [{{ "name": "Festival", "month": "Month", "description": "Why it matters" }}]
  }},
  "Budget_Insights": {{
    "Backpacker": "₹800–₹1,500",
    "Comfortable": "₹2,500–₹5,000",
    "Luxury": "₹10,000+"
  }},
  "Travel_Planning": [
    {{ "mode": "Flight", "details": "Nearest airport & typical transfer times", "booking_tip": "When to book" }},
    {{ "mode": "Train", "details": "Major stations & connectivity hubs", "booking_tip": "Quota advice" }}
  ],
  "Things_To_Do": [
    {{ "traveler_type": "Adventure", "activities": ["Specific trek name", "Specific activity"] }},
    {{ "traveler_type": "Spiritual", "activities": ["Specific temple/ashram", "Morning ritual"] }}
  ],
  "Food_And_Dining": {{
    "must_try_dishes": ["Dish Name (Description)", "Local Specialty"],
    "fine_dining": ["Specific Restaurant Name - What to order"],
    "cafe_picks": ["Hidden gem cafe names"],
    "hygiene_tips": ["Street food safety advice specific to this region"]
  }},
  "Culture_And_Heritage": {{
    "historical_context": "Deep-dive 2-sentence history of the city",
    "spiritual_sites": ["Site Name - Significance"],
    "shopping_crafts": ["What to buy & which specific market to find it"],
    "unesco_sites": [{{ "name": "Site", "status": "UNESCO/Notable", "note": "Expert tip" }}]
  }},
  "Offbeat_Gems": [
    {{ "name": "Place Name", "why_special": "Why tourists miss it", "best_for": "Photography/Solitude", "distance_from_town": "Distance" }}
  ],
  "Safety_And_Accessibility": {{
    "safety_score": 9,
    "general_tips": ["Scams to avoid", "Night safety"],
    "womens_safety": ["Specific advice for solo women"],
    "emergency_contacts": {{ "police": "100", "ambulance": "102", "hospital_name": "Best Local Hospital", "hospital_number": "Phone" }},
    "accessibility_sites": [
      {{ "site": "Landmark", "wheelchair": true, "steps_involved": "0", "mobility_notes": "Detailed ramp info" }}
    ]
  }},
  "Essential_Practicalities": {{
    "permits": ["Inner Line Permit info if applicable"],
    "currency_tips": ["ATM availability & UPI adoption level"],
    "network_coverage": "Airtel/Jio/Vi reliability",
    "health_hygiene": ["Water safety & common seasonal ailments"]
  }},
  "Day_Trips": [
    {{ "name": "Excursion Name", "highlights": "What to see", "distance_km": 45, "duration": "Full Day" }}
  ],
  "Responsible_Travel": {{
    "cultural_etiquette": ["Dress codes", "Photography taboos"],
    "sustainability_tips": ["Plastic rules", "Water conservation"],
    "support_local": ["Specific NGO or artisan collective to visit"]
  }},
  "Media_Hub": {{
    "photography_spots": ["Exact spot for the best sunrise view"],
    "books": ["One book set here"],
    "videos": ["One documentary/film reference"]
  }}
}}"""

    # 3. Call AI with your existing retry logic
    data = await generate_with_retry(prompt)

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