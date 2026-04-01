import asyncio
from backend.models.schemas import PlannerRequest
from backend.services.itinerary_engine import generate_itinerary

async def main():
    req = PlannerRequest(
        city='nyc', budget=500, duration=3, start_date='2026-05-01', end_date='2026-05-04',
        party_size='couple', mood='relaxed', dietary_preference='any',
        interests=['culture', 'food'], pace='balanced'
    )
    print('Starting generator...')
    d = await generate_itinerary(req, weather_ok=True)
    print('Done, generated days = ', len(d.days))

asyncio.run(main())
