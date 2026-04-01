import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.routers.planner import search_hotels_endpoint, search_flights_endpoint, HotelSearchRequest, FlightSearchRequest

async def main():
    print("Testing hotels...")
    req1 = HotelSearchRequest(city="nyc", nights=3, budget=500, party_size="couple", mood="relaxed")
    try:
        res = await search_hotels_endpoint(req1)
        print("Hotels:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

    print("Testing flights...")
    req2 = FlightSearchRequest(origin_city="london", destination_city="nyc", date="2026-05-01")
    try:
        res = await search_flights_endpoint(req2)
        print("Flights:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
