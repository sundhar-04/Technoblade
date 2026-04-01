import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

_AVIATIONSTACK_KEY = os.getenv("AVIATIONSTACK_API_KEY", "")
_BASE_URL = "http://api.aviationstack.com/v1/routes"

# In-memory cache to save API calls per city-pair
# Format: {"JFK_CDG": [list of flights]}
_FLIGHT_CACHE: Dict[str, List[dict]] = {}

# Comprehensive IATA mapping
_CITY_TO_IATA = {
    "nyc": ["JFK", "EWR", "LGA"],
    "new york": ["JFK", "EWR", "LGA"],
    "paris": ["CDG", "ORY"],
    "tokyo": ["HND", "NRT"],
    "london": ["LHR", "LGW"],
    "sfo": ["SFO"],
    "san francisco": ["SFO"],
    "lax": ["LAX"],
    "los angeles": ["LAX"],
    "chicago": ["ORD"],
    "miami": ["MIA"],
    "boston": ["BOS"],
    "rome": ["FCO"],
    "berlin": ["BER"]
}

def _get_iata_codes(city: str) -> List[str]:
    """Return possible IATA codes for a given city string."""
    city_key = city.lower().strip()
    return _CITY_TO_IATA.get(city_key, [city.upper().strip()[:3]])

def _heuristic_price(distance_km: float, flight_class: str) -> float:
    """Mock a realistic price based on haversine distance + class multiplier."""
    base_fare = 50.0  # airport taxes etc
    per_km_rate = 0.12 # approx 12 cents per km
    raw_price = base_fare + (distance_km * per_km_rate)
    
    # Random variance +/- 15%
    variance = random.uniform(0.85, 1.15)
    raw_price *= variance
    
    if flight_class.lower() == "business":
        raw_price *= 3.5
    elif flight_class.lower() == "first":
        raw_price *= 7.0
        
    return round(raw_price)


# Realistic airline database for mock flights
_AIRLINES_BY_ROUTE = {
    "transatlantic": [
        {"carrier": "British Airways", "iata": "BA"},
        {"carrier": "Delta Air Lines", "iata": "DL"},
        {"carrier": "American Airlines", "iata": "AA"},
        {"carrier": "United Airlines", "iata": "UA"},
        {"carrier": "Virgin Atlantic", "iata": "VS"},
    ],
    "transpacific": [
        {"carrier": "ANA (All Nippon Airways)", "iata": "NH"},
        {"carrier": "Japan Airlines", "iata": "JL"},
        {"carrier": "United Airlines", "iata": "UA"},
        {"carrier": "Delta Air Lines", "iata": "DL"},
    ],
    "europe": [
        {"carrier": "Air France", "iata": "AF"},
        {"carrier": "Lufthansa", "iata": "LH"},
        {"carrier": "British Airways", "iata": "BA"},
        {"carrier": "Alitalia", "iata": "AZ"},
    ],
    "domestic_us": [
        {"carrier": "JetBlue Airways", "iata": "B6"},
        {"carrier": "Southwest Airlines", "iata": "WN"},
        {"carrier": "Delta Air Lines", "iata": "DL"},
        {"carrier": "American Airlines", "iata": "AA"},
    ],
    "default": [
        {"carrier": "Emirates", "iata": "EK"},
        {"carrier": "Singapore Airlines", "iata": "SQ"},
        {"carrier": "Qatar Airways", "iata": "QR"},
    ],
}

# Distance estimates in km for heuristic pricing
_ROUTE_DISTANCES = {
    ("JFK", "LHR"): 5570, ("JFK", "CDG"): 5840, ("JFK", "FCO"): 6920,
    ("LHR", "JFK"): 5570, ("CDG", "JFK"): 5840, ("FCO", "JFK"): 6920,
    ("LHR", "CDG"): 340, ("CDG", "LHR"): 340, ("LHR", "FCO"): 1440,
    ("JFK", "NRT"): 10860, ("JFK", "HND"): 10860,
    ("NRT", "JFK"): 10860, ("HND", "JFK"): 10860,
    ("LHR", "NRT"): 9570, ("LHR", "HND"): 9570,
    ("SFO", "JFK"): 4150, ("SFO", "NRT"): 8280,
    ("ORD", "JFK"): 1190, ("ORD", "LHR"): 6360,
    ("BOS", "JFK"): 300, ("MIA", "JFK"): 1760,
    ("LAX", "JFK"): 3980, ("LAX", "NRT"): 8820,
    ("BER", "CDG"): 880, ("BER", "LHR"): 940, ("BER", "FCO"): 1180,
}


def _get_route_type(dep: str, arr: str) -> str:
    """Classify route type for airline selection."""
    us_airports = {"JFK", "EWR", "LGA", "SFO", "LAX", "ORD", "MIA", "BOS"}
    eu_airports = {"LHR", "LGW", "CDG", "ORY", "FCO", "BER"}
    asia_airports = {"HND", "NRT"}

    dep_region = "us" if dep in us_airports else ("eu" if dep in eu_airports else ("asia" if dep in asia_airports else "other"))
    arr_region = "us" if arr in us_airports else ("eu" if arr in eu_airports else ("asia" if arr in asia_airports else "other"))

    if dep_region == "us" and arr_region == "eu": return "transatlantic"
    if dep_region == "eu" and arr_region == "us": return "transatlantic"
    if dep_region == "us" and arr_region == "asia": return "transpacific"
    if dep_region == "asia" and arr_region == "us": return "transpacific"
    if dep_region == "eu" and arr_region == "eu": return "europe"
    if dep_region == "us" and arr_region == "us": return "domestic_us"
    return "default"


def _estimate_distance(dep: str, arr: str) -> float:
    """Estimate route distance in km."""
    return _ROUTE_DISTANCES.get((dep, arr), _ROUTE_DISTANCES.get((arr, dep), 3000.0))


def _estimate_duration(distance_km: float) -> int:
    """Estimate flight duration in minutes from distance."""
    # ~800 km/h cruise + 30 min taxi/climb/descent
    return max(60, int(distance_km / 800 * 60 + 30))


def _generate_mock_flights(dep_iata: str, arr_iata: str) -> List[dict]:
    """Generate realistic mock flight data for a given route."""
    route_type = _get_route_type(dep_iata, arr_iata)
    airlines = _AIRLINES_BY_ROUTE.get(route_type, _AIRLINES_BY_ROUTE["default"])
    distance = _estimate_distance(dep_iata, arr_iata)
    duration = _estimate_duration(distance)

    flights = []
    for airline in random.sample(airlines, min(3, len(airlines))):
        flights.append({
            "carrier": airline["carrier"],
            "iata": airline["iata"],
            "flight_number": str(random.randint(100, 9999)),
            "dep_airport": dep_iata,
            "arr_airport": arr_iata,
            "duration_min": duration + random.randint(-15, 30),
        })
    return flights


async def search_flights(origin_city: str, dest_city: str, date: str) -> List[dict]:
    """Search for scheduled flights between two cities."""
    origin_iatas = _get_iata_codes(origin_city)
    dest_iatas = _get_iata_codes(dest_city)
    
    all_flights = []
    dep_iata = origin_iatas[0]
    arr_iata = dest_iatas[0]
    
    if _AVIATIONSTACK_KEY and len(_AVIATIONSTACK_KEY) >= 20:
        # Try real API
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                cache_key = f"{dep_iata}_{arr_iata}"
                if cache_key in _FLIGHT_CACHE:
                    all_flights = _FLIGHT_CACHE[cache_key]
                else:
                    resp = await client.get(_BASE_URL, params={
                        "access_key": _AVIATIONSTACK_KEY,
                        "dep_iata": dep_iata,
                        "arr_iata": arr_iata,
                        "limit": 10
                    })
                    if resp.status_code == 200:
                        data = resp.json().get("data", [])
                        parsed = []
                        for f in data:
                            airline = f.get('airline', {})
                            flight = f.get('flight', {})
                            if flight:
                                parsed.append({
                                    "carrier": airline.get('name', 'American Airlines'),
                                    "iata": airline.get('iata', 'AA'),
                                    "flight_number": flight.get('number', str(random.randint(100, 999))),
                                    "dep_airport": dep_iata,
                                    "arr_airport": arr_iata,
                                    "duration_min": 360
                                })
                        if parsed:
                            print(f"[AVIATIONSTACK] Live API: {len(parsed)} flights found")
                        _FLIGHT_CACHE[cache_key] = parsed
                        all_flights = parsed
                    else:
                        print(f"[AVIATIONSTACK] API Error: {resp.status_code}")
        except httpx.TimeoutException:
            print("[AVIATIONSTACK] Connection timed out, using mock data")
        except Exception as e:
            print(f"[AVIATIONSTACK] Network error: {e}")
    else:
        print("[AVIATIONSTACK] No API key — using realistic mock flights")

    # Always fall back to mock if nothing from API
    if not all_flights:
        all_flights = _generate_mock_flights(dep_iata, arr_iata)

    # Inject dynamic dates and heuristic pricing
    distance = _estimate_distance(dep_iata, arr_iata)
    final_results = []
    
    for f in all_flights[:3]:
        flight_copy = f.copy()
        dep_dt = datetime.fromisoformat(date) if date else datetime.now()
        random_hour = random.randint(6, 22)
        random_min = random.choice([0, 15, 30, 45])
        dep_dt = dep_dt.replace(hour=random_hour, minute=random_min)
        arr_dt = dep_dt + timedelta(minutes=flight_copy["duration_min"])
        
        flight_copy["departure_time"] = dep_dt.isoformat()
        flight_copy["arrival_time"] = arr_dt.isoformat()
        flight_copy["price"] = _heuristic_price(distance, "economy")
        flight_copy["class"] = "economy"
        final_results.append(flight_copy)

    return final_results
