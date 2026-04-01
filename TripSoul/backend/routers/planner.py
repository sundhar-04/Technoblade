"""
Planner Router — Itinerary generation, flight search, and replanning endpoints.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from ..models.schemas import PlannerRequest
from ..services.itinerary_engine import generate_itinerary, replan_itinerary
from ..services.weather_service import get_weather, is_rainy
from ..services.adaptation_loop import get_state
from ..services.aviation_service import search_flights
from ..services.hotel_service import search_hotels
from ..models.schemas import PlannerRequest, HotelSearchRequest

router = APIRouter(prefix="/api/planner", tags=["planner"])


class FlightSearchRequest(BaseModel):
    origin_city: str
    destination_city: str
    date: str = ""


class GenerateWithFlightRequest(BaseModel):
    planner: PlannerRequest
    selected_outbound: Optional[Dict] = None
    selected_return: Optional[Dict] = None
    selected_hotel: Optional[Dict] = None


@router.post("/search-flights")
async def search_flights_endpoint(request: FlightSearchRequest):
    """Search available flights between two cities. Returns list of options."""
    print(f"[FLIGHTS] Searching: {request.origin_city} -> {request.destination_city}")
    flights = await search_flights(request.origin_city, request.destination_city, request.date)
    return {"flights": flights, "source": "api" if flights else "none"}


@router.post("/search-hotels")
async def search_hotels_endpoint(request: HotelSearchRequest):
    """Search available hotels in destination city based on preferences."""
    print(f"[HOTELS] Searching in {request.city} for {request.nights} nights, party of {request.party_size}")
    hotels = search_hotels(
        city=request.city,
        nights=request.nights,
        budget=request.budget,
        party_size=request.party_size,
        mood=request.mood
    )
    return {"hotels": hotels}


@router.post("/generate")
async def generate(request: GenerateWithFlightRequest):
    """Generate a structured itinerary with optional user-selected flights."""
    planner_req = request.planner
    print(f"DEBUG: Generating... city={planner_req.city}, origin={planner_req.origin_city}")

    weather = await get_weather(planner_req.city)
    weather_ok = not is_rainy(weather)

    try:
        itinerary = await generate_itinerary(
            planner_req,
            weather_ok=weather_ok,
            selected_outbound=request.selected_outbound,
            selected_return=request.selected_return,
            selected_hotel=request.selected_hotel,
        )
    except Exception as e:
        print(f"DEBUG: Error in generate_itinerary: {e}")
        raise

    state = get_state()
    state.set_request(planner_req)

    return {
        "itinerary": itinerary.model_dump(),
        "weather": weather,
        "weather_ok": weather_ok,
    }


@router.post("/replan")
async def replan(request: PlannerRequest):
    """Re-optimize itinerary after disruption."""
    weather = await get_weather(request.city)
    weather_ok = not is_rainy(weather)
    itinerary = await generate_itinerary(request, weather_ok=weather_ok)
    return {
        "itinerary": itinerary.model_dump(),
        "weather": weather,
        "replan_reason": "Manual replan requested",
    }
