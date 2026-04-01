import asyncio
from models.schemas import PlannerRequest
from services.itinerary_engine import generate_itinerary

async def test():
    req = PlannerRequest(
        city="nyc",
        budget=1000,
        duration=3,
        start_date="2026-05-01",
        party_size="couple",
        mood="relaxed",
        interests=["culture"]
    )
    selected_hotel = {
        "id": "htl_nyc_01",
        "name": "The Standard",
        "stars": 4, "neighborhood": "Meatpacking",
        "lat": 40.74, "lng": -74.0, "base_price": 280,
        "total_price": 840,
        "nights": 3,
        "style": "boutique"
    }
    flight_out = {
        "carrier": "Delta",
        "iata": "DL",
        "flight_number": "123",
        "price": 200,
        "duration_min": 120,
        "departure_time": "2026-05-01T08:00",
        "arrival_time": "2026-05-01T10:00"
    }
    print("Generating...")
    itinerary = await generate_itinerary(
        req, weather_ok=True,
        selected_hotel=selected_hotel,
        selected_outbound=flight_out
    )
    print("Success")

if __name__ == "__main__":
    asyncio.run(test())
