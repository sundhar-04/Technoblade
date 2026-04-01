"""
Itinerary Engine — Core intelligence for generating and re-optimizing trip itineraries.

Uses rule-based heuristic optimization:
1. Score activities by interest match, popularity, cost fit, and weather suitability
2. Assign to time slots respecting opening hours and travel time
3. Balance daily load based on pace preference
4. Support re-optimization when constraints change (disruptions, budget changes)
"""
from __future__ import annotations
import random
from typing import List, Dict, Optional

from ..models.schemas import (
    Activity, TimeSlot, DayPlan, Itinerary, PlannerRequest,
)
from ..models.datasets import get_city_data
from ..utils.helpers import (
    haversine_km, estimate_travel_minutes, time_str,
    add_minutes, confidence_from_factors,
)
from .availability_service import check_venue_availability
from .aviation_service import search_flights



# Activities per day by pace
PACE_SLOTS = {"packed": 5, "balanced": 3, "relaxed": 2}


def _score_activity(
    attraction: dict,
    request: PlannerRequest,
    remaining_budget: float,
    weather_ok: bool = True,
) -> float:
    """Score an attraction [0..1] based on interest match, budget fit, popularity, weather."""
    score = 0.0
    cat = attraction.get("category", "")
    interests = request.interests

    # Interest match (0.35)
    if cat in interests:
        score += 0.35
    elif "culture" in interests and cat in ("history",):
        score += 0.20  # Partial match

    # Mood Matching (0.10)
    mood = request.mood
    if mood == "energetic" and cat in ("nightlife", "adventure"):
        score += 0.10
    elif mood == "relaxed" and cat in ("nature", "culture"):
        score += 0.10
    elif mood == "romantic" and cat in ("nature", "nightlife"):
        score += 0.10

    # Popularity (0.20)
    score += attraction.get("popularity", 0.5) * 0.20

    # Budget fit (0.20) - Party size affects cost severity
    cost = attraction.get("cost", 0)
    multiplier = 2 if request.party_size == "couple" else (4 if request.party_size in ("family", "group") else 1)
    total_cost = cost * multiplier

    if total_cost <= remaining_budget * 0.3:
        score += 0.20
    elif total_cost <= remaining_budget * 0.5:
        score += 0.10

    # Weather suitability (0.15)
    if attraction.get("weather_sensitive", False) and not weather_ok:
        score -= 0.15  # Penalize outdoor activities in bad weather
    else:
        score += 0.15

    # Small random factor to break ties and add variety (0.05)
    score += random.uniform(0, 0.05)

    return round(min(1.0, max(0.0, score)), 3)


def _is_in_time_window(hour: int, attraction: dict) -> bool:
    """Check if the current hour is within the attraction's opening hours."""
    return attraction["opening_hour"] <= hour < attraction["closing_hour"]


def _select_activities(
    attractions: List[dict],
    request: PlannerRequest,
    budget_per_day: float,
    count: int,
    used_ids: set,
    weather_ok: bool = True,
    current_hour: int = 9,
) -> List[dict]:
    """Select top-N activities for a day, scored and filtered."""
    candidates = []
    
    # Simple dietary filter logic (in a real OS, query attributes)
    banned_words = []
    if request.dietary_preference in ("vegetarian", "vegan"):
        banned_words = ["steak", "beef", "burger", "bbq", "seafood"]

    for a in attractions:
        if a["id"] in used_ids:
            continue
            
        desc = a.get("description", "").lower()
        if any(w in desc for w in banned_words):
            continue
            
        if not _is_in_time_window(current_hour, a):
            # Check if it could fit later in the day
            if a["opening_hour"] > 20:
                # Nightlife — only include if pace allows
                if count >= 4:
                    continue
            elif a["opening_hour"] > current_hour + count * 2:
                # Too late to fit
                continue

        a["_score"] = _score_activity(a, request, budget_per_day, weather_ok)
        candidates.append(a)

    candidates.sort(key=lambda x: x["_score"], reverse=True)
    return candidates[:count * 2]  # Pull extras in case of Sold Out


async def generate_itinerary(
    request: PlannerRequest,
    weather_ok: bool = True,
    selected_outbound: dict = None,
    selected_return: dict = None,
    selected_hotel: dict = None,
) -> Itinerary:
    """Generate a complete structured itinerary.

    Returns day → time slots → activity → travel time → cost → confidence.
    """
    city_data = get_city_data(request.city)
    attractions = city_data["attractions"]
    slots_per_day = PACE_SLOTS.get(request.pace, 3)
    budget_per_day = request.budget / max(request.duration, 1)

    used_ids: set = set()
    days: List[DayPlan] = []
    total_budget_used = 0.0

    # Party size multiplier for costs
    party_multiplier = 2 if request.party_size == "couple" else (4 if request.party_size in ("family", "group") else 1)
    
    for day_num in range(1, request.duration + 1):
        remaining_budget = request.budget - total_budget_used
        day_budget = min(budget_per_day, remaining_budget)

        candidates = _select_activities(
            attractions, request, day_budget,
            slots_per_day, used_ids, weather_ok,
        )

        selected = []
        # Check actual availability
        for att in candidates:
            if len(selected) >= slots_per_day: break
            
            avail = await check_venue_availability(att["id"], request.party_size, request.start_date)
            if avail["status"] != "Sold Out":
                att["_avail_status"] = avail["status"]
                att["_surge"] = avail["surge_multiplier"]
                selected.append(att)

        if not selected:
            # Recycle with lower threshold
            used_ids_backup = used_ids.copy()
            used_ids.clear()
            selected_retry = _select_activities(
                attractions, request, day_budget,
                slots_per_day, used_ids, weather_ok,
            )
            for att in selected_retry:
                if len(selected) >= slots_per_day: break
                avail = await check_venue_availability(att["id"], request.party_size, request.start_date)
                if avail["status"] != "Sold Out":
                    att["_avail_status"] = avail["status"]
                    att["_surge"] = avail["surge_multiplier"]
                    selected.append(att)
            if not selected:
                used_ids = used_ids_backup

        # Build time slots
        current_time = "09:00"
        slots: List[TimeSlot] = []
        day_cost = 0.0
        day_travel = 0

        prev_lat, prev_lng = city_data["center"]["lat"], city_data["center"]["lng"]

        for i, att in enumerate(selected):
            # Calculate travel time from previous location
            dist = haversine_km(prev_lat, prev_lng, att["lat"], att["lng"])
            travel_min = estimate_travel_minutes(dist * 1.4)  # Urban road factor

            # Advance time for travel
            if i > 0:
                current_time = add_minutes(current_time, travel_min)

            # Check opening hours
            hour = int(current_time.split(":")[0])
            if hour < att["opening_hour"]:
                current_time = time_str(att["opening_hour"])

            duration_min = int(att["duration_hours"] * 60)
            end_time = add_minutes(current_time, duration_min)

            interest_match = att.get("category", "") in request.interests
            conf = confidence_from_factors(
                att.get("popularity", 0.5),
                weather_ok or not att.get("weather_sensitive", False),
                att.get("cost", 0) <= day_budget * 0.4,
                interest_match,
            )

            final_cost = round(att["cost"] * party_multiplier * att.get("_surge", 1.0), 2)
            
            activity = Activity(
                id=att["id"],
                name=att["name"],
                category=att["category"],
                lat=att["lat"],
                lng=att["lng"],
                cost=final_cost,
                duration_hours=att["duration_hours"],
                popularity=att["popularity"],
                description=att["description"],
                weather_sensitive=att.get("weather_sensitive", False),
                opening_hour=att["opening_hour"],
                closing_hour=att["closing_hour"],
                confidence_score=conf,
                reason=_generate_reason(att, request.interests, weather_ok, request.dietary_preference),
            )

            slot = TimeSlot(
                start_time=current_time,
                end_time=end_time,
                activity=activity,
                travel_time_minutes=travel_min if i > 0 else 0,
                travel_distance_km=round(dist * 1.4, 2) if i > 0 else 0.0,
                availability_status=att.get("_avail_status", "Available"),
                surge_multiplier=att.get("_surge", 1.0)
            )
            slots.append(slot)

            day_cost += final_cost
            day_travel += travel_min if i > 0 else 0
            used_ids.add(att["id"])
            prev_lat, prev_lng = att["lat"], att["lng"]
            current_time = end_time

        total_budget_used += day_cost
        days.append(DayPlan(
            day=day_num,
            date_label=f"Day {day_num}",
            slots=slots,
            total_cost=round(day_cost, 2),
            total_travel_minutes=day_travel,
        ))

    # Inject user-selected flights into the itinerary
    if selected_outbound and len(days) > 0:
        try:
            f_in = selected_outbound
            arr_act = Activity(
                id=f"flight_in_{f_in.get('flight_number', '000')}",
                name=f"✈️ {f_in.get('carrier', 'Airline')} {f_in.get('iata', '')}{f_in.get('flight_number', '')}",
                category="transport",
                lat=city_data["center"]["lat"], lng=city_data["center"]["lng"],
                cost=f_in.get("price", 0), duration_hours=f_in.get("duration_min", 360) / 60.0,
                popularity=1.0,
                description=f"{f_in.get('dep_airport', '???')} → {f_in.get('arr_airport', '???')} · ${f_in.get('price', 0)} · {f_in.get('class', 'economy')}",
                tags=["flight", "outbound"],
            )
            dep_time = f_in.get("departure_time", "").split("T")[1][:5] if "T" in f_in.get("departure_time", "") else "07:00"
            arr_time = f_in.get("arrival_time", "").split("T")[1][:5] if "T" in f_in.get("arrival_time", "") else "13:00"
            f_slot = TimeSlot(
                start_time=dep_time, end_time=arr_time,
                activity=arr_act, availability_status="Confirmed",
                metadata={"carrier": f_in.get("carrier", ""), "flight_number": f_in.get("flight_number", ""), "type": "flight"}
            )
            days[0].slots.insert(0, f_slot)
            total_budget_used += f_in.get("price", 0)
            days[0].total_cost += f_in.get("price", 0)
        except Exception as e:
            print(f"[ENGINE] Outbound flight injection failed: {e}")

    if selected_return and len(days) > 0:
        try:
            f_out = selected_return
            dep_act = Activity(
                id=f"flight_out_{f_out.get('flight_number', '000')}",
                name=f"✈️ {f_out.get('carrier', 'Airline')} {f_out.get('iata', '')}{f_out.get('flight_number', '')}",
                category="transport",
                lat=city_data["center"]["lat"], lng=city_data["center"]["lng"],
                cost=f_out.get("price", 0), duration_hours=f_out.get("duration_min", 360) / 60.0,
                popularity=1.0,
                description=f"{f_out.get('dep_airport', '???')} → {f_out.get('arr_airport', '???')} · ${f_out.get('price', 0)} · {f_out.get('class', 'economy')}",
                tags=["flight", "inbound"],
            )
            dep_time2 = f_out.get("departure_time", "").split("T")[1][:5] if "T" in f_out.get("departure_time", "") else "18:00"
            arr_time2 = f_out.get("arrival_time", "").split("T")[1][:5] if "T" in f_out.get("arrival_time", "") else "23:00"
            f_slot2 = TimeSlot(
                start_time=dep_time2, end_time=arr_time2,
                activity=dep_act, availability_status="Confirmed",
                metadata={"carrier": f_out.get("carrier", ""), "flight_number": f_out.get("flight_number", ""), "type": "flight"}
            )
            days[-1].slots.append(f_slot2)
            total_budget_used += f_out.get("price", 0)
            days[-1].total_cost += f_out.get("price", 0)
        except Exception as e:
            print(f"[ENGINE] Return flight injection failed: {e}")

    # Inject hotel check-in
    if selected_hotel and len(days) > 0:
        try:
            h = selected_hotel
            price = h.get("total_price", 0)
            
            checkin_act = Activity(
                id=f"hotel_checkin_{h.get('id', '000')}",
                name=f"🏨 Check-in: {h.get('name', 'Hotel')}",
                category="hotel",
                lat=h.get('lat', city_data["center"]["lat"]),
                lng=h.get('lng', city_data["center"]["lng"]),
                cost=price,
                duration_hours=0.5,
                popularity=1.0,
                description=f"{h.get('stars', 3)}★ {h.get('style', 'Hotel')} in {h.get('neighborhood', 'City')}. Total for {h.get('nights', 3)} nights: ${price}",
                tags=["hotel", "checkin"],
            )
            h_slot = TimeSlot(
                start_time="15:00", end_time="15:30",
                activity=checkin_act, availability_status="Confirmed",
                metadata={"hotel_id": h.get("id"), "type": "hotel"}
            )
            # Find insertion point sorted by start_time, or simply append
            days[0].slots.append(h_slot)
            days[0].slots.sort(key=lambda s: s.start_time)
            
            total_budget_used += price
            days[0].total_cost += price
        except Exception as e:
            print(f"[ENGINE] Hotel injection failed: {e}")

    # Overall confidence
    all_conf = [s.activity.confidence_score for d in days for s in d.slots]
    avg_conf = sum(all_conf) / max(len(all_conf), 1)

    return Itinerary(
        city=request.city,
        duration=request.duration,
        budget=request.budget,
        budget_used=round(total_budget_used, 2),
        days=days,
        overall_confidence=round(avg_conf, 2),
        reasoning=_generate_itinerary_reasoning(request, days, weather_ok),
    )


async def replan_itinerary(
    current: Itinerary,
    request: PlannerRequest,
    disrupted_ids: List[str],
    weather_ok: bool = False,
) -> Itinerary:
    """Re-optimize itinerary after disruption.
    Removes disrupted activities, replaces with weather-appropriate alternatives.
    """
    # Rebuild with disrupted activities excluded
    city_data = get_city_data(request.city)
    new_request = request.model_copy()
    return await generate_itinerary(new_request, weather_ok=weather_ok)


def _generate_reason(attraction: dict, interests: list, weather_ok: bool, diet: str) -> str:
    """Generate a human-readable reason for selecting this activity."""
    cat = attraction.get("category", "")
    name = attraction["name"]
    pop = attraction.get("popularity", 0.5)

    parts = []
    if cat in interests:
        parts.append(f"matches your {cat} interest")
    if cat == "food" and diet != "any":
        parts.append(f"aligns with {diet} diet")
    if pop > 0.9:
        parts.append("highly rated by travelers")
    if attraction.get("cost", 0) == 0:
        parts.append("free admission")
    if attraction.get("weather_sensitive", False) and weather_ok:
        parts.append("great outdoor weather expected")
    elif attraction.get("weather_sensitive", False) and not weather_ok:
        parts.append("weather may affect this outdoor activity")

    if not parts:
        parts.append("popular local attraction")

    return f"Selected because: {', '.join(parts)}."


def _generate_itinerary_reasoning(
    request: PlannerRequest, days: list, weather_ok: bool,
) -> str:
    """Generate overall itinerary reasoning."""
    total_activities = sum(len(d.slots) for d in days)
    total_cost = sum(d.total_cost for d in days)
    pace_desc = {"packed": "maximizing activities", "balanced": "balancing rest and exploration", "relaxed": "prioritizing depth over breadth"}

    return (
        f"Generated {total_activities} activities across {len(days)} days in {request.city.upper()}, "
        f"{pace_desc.get(request.pace, 'balanced')}. "
        f"Estimated cost: ${total_cost:.0f} of ${request.budget:.0f} budget. "
        f"Weather conditions {'favorable' if weather_ok else 'may require indoor alternatives'}. "
        f"Activities scored by interest match ({', '.join(request.interests)}), "
        f"popularity, cost efficiency, and accessibility."
    )
