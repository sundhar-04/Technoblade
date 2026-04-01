"""
TripSoul AI Travel Operating System — FastAPI Backend

An intelligent travel OS that autonomously plans, optimizes, and adapts
trips in real time using decision intelligence.

Modules:
- /api/planner         — Itinerary generation with heuristic optimization
- /api/personalization — Cosine similarity recommender with implicit feedback
- /api/optimization    — Multi-objective knapsack budget optimizer
- /api/prediction      — Delay estimation with congestion+weather factors
- /api/adaptation      — Background disruption detection + SSE live updates
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .routers import planner, personalization, optimization, prediction, adaptation
from .services.adaptation_loop import start_adaptation_loop, stop_adaptation_loop
from .models.datasets import get_available_cities

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: launch adaptation loop. Shutdown: cleanly stop it."""
    await start_adaptation_loop()
    print("[TRIPSOUL] AI Travel OS online — adaptation loop active")
    yield
    await stop_adaptation_loop()
    print("[TRIPSOUL] Shutting down")


app = FastAPI(
    title="TripSoul AI Travel OS",
    description="Intelligent travel operating system with decision intelligence",
    version="5.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(planner.router)
app.include_router(personalization.router)
app.include_router(optimization.router)
app.include_router(prediction.router)
app.include_router(adaptation.router)


@app.get("/")
async def root():
    """Health check and system info."""
    return {
        "system": "TripSoul AI Travel OS",
        "version": "5.0.0",
        "status": "online",
        "modules": [
            "planner", "personalization", "optimization",
            "prediction", "adaptation",
        ],
        "cities": get_available_cities(),
        "apis": {
            "weather": "active" if os.getenv("OPENWEATHER_API_KEY") else "mock",
            "maps": "active" if os.getenv("GOOGLE_MAPS_API_KEY") else "mock",
        },
    }


@app.get("/api/cities")
async def cities():
    """List available cities with basic info."""
    from .models.datasets import CITY_DATA
    return {
        key: {
            "name": data["name"],
            "country": data["country"],
            "center": data["center"],
            "attraction_count": len(data["attractions"]),
        }
        for key, data in CITY_DATA.items()
    }

from pydantic import BaseModel
from typing import Optional, List

class PlaceSuggestionRequest(BaseModel):
    city: str
    day_theme: Optional[str] = ""
    existing_places: Optional[List[str]] = []
    mood: Optional[str] = ""
    interests: Optional[List[str]] = []

@app.post("/suggest-places")
async def suggest_places(req: PlaceSuggestionRequest):
    from .models.datasets import get_city_data
    try:
        city_data = get_city_data(req.city)
        attractions = city_data["attractions"]
    except KeyError:
        attractions = []
        
    # Heuristic filtering
    query = req.day_theme.lower() if req.day_theme else ""
    existing = set(req.existing_places or [])
    
    candidates = []
    for a in attractions:
        if a["name"] in existing:
            continue
        
        # Matches query?
        if query and query not in a["name"].lower() and query not in a.get("category", "").lower():
            continue
            
        candidates.append({
            "name": a["name"],
            "category": a.get("category", "culture"),
            "description": a.get("description", f"Visit {a['name']}."),
            "estimated_duration_minutes": int(a.get("duration_hours", 1.5) * 60),
            "cost": a.get("cost", 0),
            "reason": "Matches your search criteria.",
            "lat": a["lat"],
            "lng": a["lng"]
        })
        
        if len(candidates) >= 5:
            break
            
    if not candidates:
        # Fallback suggestions
        candidates = [
            {"name": f"{req.city} Heritage Walk", "category": "culture", "description": f"A guided walking tour through the historic lanes of {req.city}.", "estimated_duration_minutes": 120, "cost": 300, "reason": "Great way to understand the city's soul.", "lat": 40.730610, "lng": -73.935242},
            {"name": f"Local Street Food Trail", "category": "food", "description": f"Taste the best street food {req.city} has to offer.", "estimated_duration_minutes": 90, "cost": 200, "reason": "No trip is complete without local flavours.", "lat": 40.730610, "lng": -73.935242},
        ]
        
    return {"suggestions": candidates}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

