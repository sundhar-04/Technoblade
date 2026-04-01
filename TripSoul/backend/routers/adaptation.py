"""
Adaptation Router — Disruption detection, SSE events, and simulation.
"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..models.schemas import SimulateRequest
from ..services.adaptation_loop import (
    get_current_status, simulate_disruption, event_stream,
)

router = APIRouter(prefix="/api/adaptation", tags=["adaptation"])


@router.get("/status")
async def status():
    """Get current adaptation system status.

    Returns active disruptions, last weather check, and
    whether an adapted plan exists.
    """
    return get_current_status()


@router.get("/events")
async def events():
    """SSE endpoint for live disruption updates.

    Frontend connects to this endpoint and receives real-time
    notifications when:
    - Weather disruption detected
    - Itinerary automatically re-optimized
    - Venue closure or delay detected

    The system adapts WITHOUT user request.
    """
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/simulate")
async def simulate(request: SimulateRequest):
    """Simulate a disruption for demo purposes.

    Types:
    - 'weather': Heavy rain scenario
    - 'closure': Unexpected venue closure
    - 'delay': Transit delay in central zone

    If an active itinerary exists, automatically
    re-optimizes and pushes update via SSE.
    """
    result = await simulate_disruption(request)
    return result
