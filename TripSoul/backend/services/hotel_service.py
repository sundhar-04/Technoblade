"""
Hotel Service — Smart accommodation recommendations with pricing heuristics.

Generates realistic hotel options per city based on budget, party size, and mood.
In production, this would connect to Booking.com, Expedia, or Amadeus APIs.
"""
import random
from typing import List, Dict

# Curated hotel database per city with realistic data
HOTEL_DATABASE: Dict[str, List[dict]] = {
    "nyc": [
        {"id": "htl_nyc_01", "name": "The Standard, High Line", "stars": 4, "neighborhood": "Meatpacking District", "lat": 40.7409, "lng": -74.0080, "base_price": 280, "amenities": ["rooftop bar", "spa", "gym"], "style": "boutique", "rating": 4.3, "image_tag": "modern-glass-hotel"},
        {"id": "htl_nyc_02", "name": "The Plaza Hotel", "stars": 5, "neighborhood": "Midtown", "lat": 40.7645, "lng": -73.9744, "base_price": 650, "amenities": ["spa", "fine dining", "butler service"], "style": "luxury", "rating": 4.7, "image_tag": "grand-classic-hotel"},
        {"id": "htl_nyc_03", "name": "Pod 51", "stars": 3, "neighborhood": "Midtown East", "lat": 40.7553, "lng": -73.9680, "base_price": 120, "amenities": ["rooftop", "cafe"], "style": "budget", "rating": 4.0, "image_tag": "pod-hotel"},
        {"id": "htl_nyc_04", "name": "The Greenwich Hotel", "stars": 5, "neighborhood": "Tribeca", "lat": 40.7196, "lng": -74.0104, "base_price": 550, "amenities": ["spa", "pool", "restaurant"], "style": "luxury", "rating": 4.8, "image_tag": "luxury-downtown"},
        {"id": "htl_nyc_05", "name": "citizenM New York Bowery", "stars": 4, "neighborhood": "Lower East Side", "lat": 40.7204, "lng": -73.9934, "base_price": 180, "amenities": ["rooftop bar", "coworking", "gym"], "style": "modern", "rating": 4.4, "image_tag": "citizenm-modern"},
        {"id": "htl_nyc_06", "name": "YOTEL New York", "stars": 3, "neighborhood": "Hell's Kitchen", "lat": 40.7607, "lng": -73.9948, "base_price": 140, "amenities": ["terrace", "gym", "robot luggage"], "style": "tech", "rating": 4.1, "image_tag": "yotel-futuristic"},
    ],
    "tokyo": [
        {"id": "htl_tyo_01", "name": "Park Hyatt Tokyo", "stars": 5, "neighborhood": "Shinjuku", "lat": 35.6867, "lng": 139.6917, "base_price": 480, "amenities": ["spa", "pool", "New York Bar"], "style": "luxury", "rating": 4.8, "image_tag": "park-hyatt"},
        {"id": "htl_tyo_02", "name": "Trunk Hotel", "stars": 4, "neighborhood": "Shibuya", "lat": 35.6620, "lng": 139.7074, "base_price": 250, "amenities": ["rooftop", "restaurant", "lounge"], "style": "boutique", "rating": 4.5, "image_tag": "trunk-hotel"},
        {"id": "htl_tyo_03", "name": "Capsule Hotel Anshin Oyado", "stars": 2, "neighborhood": "Shinjuku", "lat": 35.6918, "lng": 139.7002, "base_price": 35, "amenities": ["sauna", "manga library"], "style": "capsule", "rating": 4.0, "image_tag": "capsule-hotel"},
        {"id": "htl_tyo_04", "name": "Aman Tokyo", "stars": 5, "neighborhood": "Otemachi", "lat": 35.6871, "lng": 139.7637, "base_price": 750, "amenities": ["spa", "pool", "fine dining", "zen garden"], "style": "ultra-luxury", "rating": 4.9, "image_tag": "aman-tokyo"},
        {"id": "htl_tyo_05", "name": "THE KNOT Tokyo Shinjuku", "stars": 3, "neighborhood": "Shinjuku", "lat": 35.6934, "lng": 139.6952, "base_price": 90, "amenities": ["cafe", "lounge", "bike rental"], "style": "modern", "rating": 4.2, "image_tag": "knot-hotel"},
        {"id": "htl_tyo_06", "name": "Mitsui Garden Hotel Ginza", "stars": 4, "neighborhood": "Ginza", "lat": 35.6718, "lng": 139.7674, "base_price": 180, "amenities": ["onsen", "restaurant"], "style": "traditional-modern", "rating": 4.4, "image_tag": "mitsui-garden"},
    ],
    "paris": [
        {"id": "htl_par_01", "name": "Hôtel Plaza Athénée", "stars": 5, "neighborhood": "8th Arrondissement", "lat": 48.8660, "lng": 2.3037, "base_price": 800, "amenities": ["Alain Ducasse restaurant", "spa", "Eiffel view"], "style": "palace", "rating": 4.9, "image_tag": "plaza-athenee"},
        {"id": "htl_par_02", "name": "Le Citizen Hotel", "stars": 4, "neighborhood": "Canal Saint-Martin", "lat": 48.8714, "lng": 2.3651, "base_price": 200, "amenities": ["canal view", "iPad concierge", "breakfast"], "style": "boutique", "rating": 4.4, "image_tag": "citizen-paris"},
        {"id": "htl_par_03", "name": "Generator Paris", "stars": 2, "neighborhood": "10th Arrondissement", "lat": 48.8813, "lng": 2.3700, "base_price": 60, "amenities": ["bar", "terrace", "coworking"], "style": "hostel-chic", "rating": 4.0, "image_tag": "generator-hostel"},
        {"id": "htl_par_04", "name": "Le Marais Boutique Hotel", "stars": 4, "neighborhood": "Le Marais", "lat": 48.8566, "lng": 2.3622, "base_price": 260, "amenities": ["courtyard", "wine bar", "concierge"], "style": "boutique", "rating": 4.6, "image_tag": "marais-boutique"},
        {"id": "htl_par_05", "name": "Mama Shelter Paris", "stars": 3, "neighborhood": "20th Arrondissement", "lat": 48.8580, "lng": 2.3920, "base_price": 110, "amenities": ["rooftop", "restaurant", "entertainment"], "style": "trendy", "rating": 4.2, "image_tag": "mama-shelter"},
        {"id": "htl_par_06", "name": "The Ritz Paris", "stars": 5, "neighborhood": "1st Arrondissement", "lat": 48.8683, "lng": 2.3288, "base_price": 1100, "amenities": ["Hemingway Bar", "spa", "pool", "garden"], "style": "palace", "rating": 4.9, "image_tag": "ritz-paris"},
    ],
    "london": [
        {"id": "htl_lon_01", "name": "The Ned", "stars": 5, "neighborhood": "City of London", "lat": 51.5134, "lng": -0.0876, "base_price": 380, "amenities": ["rooftop pool", "9 restaurants", "spa"], "style": "grand", "rating": 4.7, "image_tag": "the-ned"},
        {"id": "htl_lon_02", "name": "citizenM Tower of London", "stars": 4, "neighborhood": "Tower Hill", "lat": 51.5100, "lng": -0.0764, "base_price": 160, "amenities": ["rooftop bar", "smart rooms"], "style": "modern", "rating": 4.4, "image_tag": "citizenm-london"},
        {"id": "htl_lon_03", "name": "Generator London", "stars": 2, "neighborhood": "King's Cross", "lat": 51.5303, "lng": -0.1222, "base_price": 50, "amenities": ["bar", "games room"], "style": "hostel-chic", "rating": 3.9, "image_tag": "generator-london"},
        {"id": "htl_lon_04", "name": "The Savoy", "stars": 5, "neighborhood": "Strand", "lat": 51.5105, "lng": -0.1204, "base_price": 600, "amenities": ["river view", "pool", "spa", "afternoon tea"], "style": "luxury", "rating": 4.8, "image_tag": "savoy-hotel"},
        {"id": "htl_lon_05", "name": "Hoxton Shoreditch", "stars": 4, "neighborhood": "Shoreditch", "lat": 51.5255, "lng": -0.0810, "base_price": 170, "amenities": ["restaurant", "bar", "workspace"], "style": "boutique", "rating": 4.3, "image_tag": "hoxton-hotel"},
    ],
    "rome": [
        {"id": "htl_rom_01", "name": "Hotel de Russie", "stars": 5, "neighborhood": "Piazza del Popolo", "lat": 41.9108, "lng": 12.4762, "base_price": 450, "amenities": ["secret garden", "spa", "Stravinskij Bar"], "style": "luxury", "rating": 4.7, "image_tag": "de-russie"},
        {"id": "htl_rom_02", "name": "The Fifteen Keys Hotel", "stars": 4, "neighborhood": "Rione Monti", "lat": 41.8990, "lng": 12.4922, "base_price": 200, "amenities": ["courtyard", "bar", "breakfast"], "style": "boutique", "rating": 4.5, "image_tag": "fifteen-keys"},
        {"id": "htl_rom_03", "name": "The Yellow Hostel", "stars": 2, "neighborhood": "Termini", "lat": 41.9028, "lng": 12.5010, "base_price": 40, "amenities": ["bar", "restaurant", "events"], "style": "hostel", "rating": 4.1, "image_tag": "yellow-hostel"},
        {"id": "htl_rom_04", "name": "Hotel Raphael", "stars": 5, "neighborhood": "Piazza Navona", "lat": 41.8992, "lng": 12.4731, "base_price": 500, "amenities": ["rooftop terrace", "art collection", "restaurant"], "style": "art-hotel", "rating": 4.6, "image_tag": "hotel-raphael"},
        {"id": "htl_rom_05", "name": "Chapter Roma", "stars": 4, "neighborhood": "Campo de' Fiori", "lat": 41.8955, "lng": 12.4720, "base_price": 180, "amenities": ["rooftop pool", "bar", "gym"], "style": "modern", "rating": 4.4, "image_tag": "chapter-roma"},
    ],
}


def _price_for_nights(base_price: float, nights: int, party_size: str, mood: str) -> float:
    """Calculate total hotel cost with modifiers."""
    # Party size multiplier (suite vs single)
    size_mult = {
        "solo": 0.85, "couple": 1.0, "family": 1.4, "group": 1.6
    }.get(party_size, 1.0)

    # Mood-based preference weight (romantic = pays more for ambiance)
    mood_mult = {
        "romantic": 1.15, "relaxed": 1.05, "energetic": 0.95, "family": 1.0
    }.get(mood, 1.0)

    # Slight variance per query
    variance = random.uniform(0.9, 1.1)

    nightly = base_price * size_mult * mood_mult * variance
    return round(nightly * nights, 2)


def search_hotels(
    city: str,
    nights: int = 3,
    budget: float = 500,
    party_size: str = "couple",
    mood: str = "relaxed",
) -> List[dict]:
    """Return ranked hotel options for a city within budget constraints.
    
    Hotels are scored and ranked by:
    - Budget fit (largest weight)
    - Rating / stars
    - Mood alignment
    """
    city_key = city.lower().strip()
    hotels = HOTEL_DATABASE.get(city_key, HOTEL_DATABASE.get("nyc", []))

    # Budget allocated to accommodation (~35% of total trip budget)
    hotel_budget = budget * 0.35

    results = []
    for h in hotels:
        total = _price_for_nights(h["base_price"], nights, party_size, mood)
        nightly = total / max(nights, 1)

        # Budget fit score (0..1)
        if total <= hotel_budget:
            budget_score = 1.0 - (total / max(hotel_budget, 1)) * 0.3
        elif total <= hotel_budget * 1.5:
            budget_score = 0.5
        else:
            budget_score = 0.2

        # Rating score
        rating_score = h["rating"] / 5.0

        # Mood matching
        mood_match = 0.5
        if mood == "romantic" and h["style"] in ("boutique", "luxury", "palace", "ultra-luxury"):
            mood_match = 1.0
        elif mood == "energetic" and h["style"] in ("modern", "tech", "trendy", "hostel-chic"):
            mood_match = 1.0
        elif mood == "relaxed" and h["style"] in ("boutique", "luxury", "traditional-modern"):
            mood_match = 0.9
        elif mood == "family" and h["stars"] >= 4:
            mood_match = 0.9

        composite = budget_score * 0.4 + rating_score * 0.35 + mood_match * 0.25

        results.append({
            **h,
            "total_price": total,
            "nightly_price": round(nightly),
            "nights": nights,
            "match_score": round(composite, 2),
            "budget_fit": "within" if total <= hotel_budget else ("stretch" if total <= hotel_budget * 1.5 else "over"),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:4]  # Return top 4 options
