"""
Planner Router — Itinerary generation and replanning endpoints.
"""
from fastapi import APIRouter
from ..models.schemas import PlannerRequest
from ..services.itinerary_engine import generate_itinerary, replan_itinerary
from ..services.weather_service import get_weather, is_rainy
from ..services.adaptation_loop import get_state

router = APIRouter(prefix="/api/planner", tags=["planner"])


@router.post("/generate")
async def generate(request: PlannerRequest):
    print(f"DEBUG: Generating... request={request}")
    """Generate a structured itinerary.

    Input: city, budget, duration, interests, pace.
    Output: day → time slots → activity → travel time → cost → confidence score.
    """
    # Check current weather for the city
    weather = await get_weather(request.city)
    weather_ok = not is_rainy(weather)

    try:
        print("DEBUG: Before generate_itinerary")
        itinerary = await generate_itinerary(request, weather_ok=weather_ok)
        print("DEBUG: After generate_itinerary")
    except Exception as e:
        print(f"DEBUG: Error in generate_itinerary: {e}")
        raise

    # Register with adaptation loop
    state = get_state()
    state.set_request(request)

    return {
        "itinerary": itinerary.model_dump(),
        "weather": weather,
        "weather_ok": weather_ok,
    }


@router.post("/replan")
async def replan(request: PlannerRequest):
    """Re-optimize itinerary after disruption.

    Accepts the same input as /generate plus disruption context.
    Returns recomputed itinerary with changed activities and explanation.
    """
    weather = await get_weather(request.city)
    weather_ok = not is_rainy(weather)

    itinerary = await generate_itinerary(request, weather_ok=weather_ok)

    return {
        "itinerary": itinerary.model_dump(),
        "weather": weather,
        "replan_reason": "Manual replan requested",
    }
