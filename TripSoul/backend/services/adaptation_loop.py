"""
Adaptation Loop — Background async service for real-time disruption detection.

Continuously:
1. Polls weather data every 30 seconds
2. Detects disruptions (rain > threshold, high congestion)
3. Triggers itinerary re-optimization
4. Pushes updates to connected frontends via SSE

Also supports manual disruption simulation for demo purposes.
"""
from __future__ import annotations
import asyncio
import json
from typing import Optional, AsyncGenerator, List
from datetime import datetime

from ..models.schemas import (
    DisruptionEvent, AdaptationResponse, PlannerRequest, SimulateRequest,
)
from ..utils.helpers import current_timestamp
from ..utils.mock_data import get_mock_disruption
from .weather_service import get_weather, is_rainy, weather_impact_factor
from .itinerary_engine import generate_itinerary


# ── State ────────────────────────────────────────────────────────────────────

class AdaptationState:
    """Global adaptation state — tracks current disruptions, itineraries, and SSE subscribers."""

    def __init__(self):
        self.current_disruptions: List[DisruptionEvent] = []
        self.last_weather: dict = {}
        self.current_city: str = "nyc"
        self.current_request: Optional[PlannerRequest] = None
        self.last_adapted_plan: Optional[dict] = None
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None

    async def push_event(self, event: dict):
        """Push an event to all SSE subscribers."""
        await self.event_queue.put(event)

    def set_request(self, request: PlannerRequest):
        """Update the current active itinerary request."""
        self.current_request = request
        self.current_city = request.city


_state = AdaptationState()


def get_state() -> AdaptationState:
    return _state


# ── Background Poller ────────────────────────────────────────────────────────

async def _poll_loop():
    """Background loop: check weather every 30s, detect disruptions."""
    state = get_state()
    state._running = True
    print("[ADAPTATION] Background loop started")

    while state._running:
        try:
            weather = await get_weather(state.current_city)
            state.last_weather = weather

            # Check for weather disruption
            if is_rainy(weather) and weather.get("rain_mm", 0) > 5:
                disruption = DisruptionEvent(
                    type="weather",
                    severity="high" if weather["rain_mm"] > 10 else "medium",
                    description=f"Rain detected: {weather['rain_mm']}mm, {weather['rain_probability']*100:.0f}% probability",
                    timestamp=current_timestamp(),
                )

                # Only trigger if this is new
                if not any(d.type == "weather" and d.severity == disruption.severity
                          for d in state.current_disruptions):
                    state.current_disruptions.append(disruption)

                    # Trigger re-optimization if we have an active plan
                    if state.current_request:
                        adapted = await _reoptimize(state.current_request, disruption, weather)
                        await state.push_event({
                            "type": "disruption",
                            "data": adapted,
                        })

        except Exception as e:
            print(f"[ADAPTATION] Poll error: {e}")

        await asyncio.sleep(30)


async def start_adaptation_loop():
    """Start the background adaptation polling loop."""
    state = get_state()
    if state._task is None or state._task.done():
        state._task = asyncio.create_task(_poll_loop())


async def stop_adaptation_loop():
    """Stop the background polling loop."""
    state = get_state()
    state._running = False
    if state._task:
        state._task.cancel()


# ── Re-optimization ──────────────────────────────────────────────────────────

async def _reoptimize(
    request: PlannerRequest,
    disruption: DisruptionEvent,
    weather: dict,
) -> dict:
    """Re-optimize itinerary after disruption detected."""
    weather_ok = not is_rainy(weather)
    new_plan = await generate_itinerary(request, weather_ok=weather_ok)

    changes = []
    if disruption.type == "weather":
        changes.append("Replaced outdoor activities with indoor alternatives")
        changes.append(f"Adjusted for {weather.get('description', 'bad weather')}")
    elif disruption.type == "closure":
        changes.append("Removed closed venue and substituted alternatives")
    elif disruption.type == "delay":
        changes.append("Reduced activities to accommodate transit delays")

    reasoning = (
        f"Disruption detected: {disruption.description}. "
        f"Itinerary automatically re-optimized. Changes: {'; '.join(changes)}. "
        f"The system prioritized {'indoor' if disruption.type == 'weather' else 'accessible'} "
        f"activities with minimal travel time."
    )

    result = AdaptationResponse(
        disruption=disruption,
        adapted_plan=new_plan,
        changes_made=changes,
        reasoning=reasoning,
    )

    state = get_state()
    state.last_adapted_plan = result.model_dump()
    return result.model_dump()


# ── Simulation ───────────────────────────────────────────────────────────────

async def simulate_disruption(sim: SimulateRequest) -> dict:
    """Manually trigger a disruption for demo purposes."""
    state = get_state()
    mock = get_mock_disruption(sim.disruption_type)

    disruption = DisruptionEvent(
        type=mock["type"],
        severity=sim.severity or mock.get("severity", "medium"),
        description=mock["description"],
        timestamp=current_timestamp(),
    )
    state.current_disruptions.append(disruption)

    # If we have an active request, re-optimize
    if state.current_request:
        weather = state.last_weather or await get_weather(sim.city)
        # For weather simulation, override weather data
        if sim.disruption_type == "weather":
            weather.update(mock.get("condition_override", {}))

        adapted = await _reoptimize(state.current_request, disruption, weather)
        await state.push_event({"type": "disruption", "data": adapted})
        return adapted

    return AdaptationResponse(
        disruption=disruption,
        changes_made=["No active itinerary to adapt — disruption logged"],
        reasoning="Generate an itinerary first, then simulate disruptions to see adaptation.",
    ).model_dump()


# ── SSE Stream ───────────────────────────────────────────────────────────────

async def event_stream() -> AsyncGenerator[str, None]:
    """Server-Sent Events generator for live disruption updates."""
    state = get_state()

    # Send initial status
    yield f"data: {json.dumps({'type': 'connected', 'city': state.current_city})}\n\n"

    while True:
        try:
            event = await asyncio.wait_for(state.event_queue.get(), timeout=15.0)
            yield f"data: {json.dumps(event, default=str)}\n\n"
        except asyncio.TimeoutError:
            # Keep-alive ping
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
        except Exception:
            break


def get_current_status() -> dict:
    """Return current adaptation status."""
    state = get_state()
    return {
        "active": state._running,
        "city": state.current_city,
        "disruptions": [d.model_dump() for d in state.current_disruptions],
        "last_weather": state.last_weather,
        "has_adapted_plan": state.last_adapted_plan is not None,
    }
