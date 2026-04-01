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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
