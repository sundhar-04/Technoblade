"""
Mock Availability Service for TripSoul.
Simulates real-time checking of flights, hotels, and venues.
In an enterprise OS, this connects to Amadeus or directly to OTAs.
"""
import random
import asyncio
from typing import Dict, Any

async def check_venue_availability(activity_id: str, party_size: str, date: str) -> Dict[str, Any]:
    """
    Simulates checking a restaurant or attraction's booking system.
    Returns status: Available, Limited, Sold Out, and a dynamic price multiplier.
    """
    # Artificial delay to simulate real API call
    await asyncio.sleep(0.1)

    # Some deterministic pseudorandomness based on id and party_size
    seed_str = f"{activity_id}_{date}_{party_size}"
    rng = random.Random(seed_str)
    
    rand_val = rng.random()
    
    status = "Available"
    multiplier = 1.0
    
    if rand_val > 0.85:
        status = "Sold Out"
    elif rand_val > 0.6:
        status = "Limited"
        # Surge pricing for limited availability
        multiplier = round(rng.uniform(1.1, 1.5), 2)
        
    return {
        "status": status,
        "surge_multiplier": multiplier,
        "checked_at": "real-time"
    }
