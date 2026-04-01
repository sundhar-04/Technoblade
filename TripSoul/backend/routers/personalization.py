"""
Personalization Router — User preference tracking and recommendations.
"""
from fastapi import APIRouter
from ..models.schemas import UserFeedback
from ..models.datasets import get_city_data
from ..services.personalization_engine import (
    track_feedback, get_recommendations, get_profile_summary,
)

router = APIRouter(prefix="/api/personalization", tags=["personalization"])


@router.post("/track")
async def track(feedback: UserFeedback):
    """Log implicit user feedback: clicks, saves, dwell time.

    Automatically updates the user's preference vector using
    weighted category scoring.
    """
    # Look up the activity to get its category
    for city_key in ("nyc", "tokyo", "paris"):
        city_data = get_city_data(city_key)
        for att in city_data.get("attractions", []):
            if att["id"] == feedback.activity_id:
                return track_feedback(feedback, att)

    # Activity not found in datasets — still update with generic info
    return track_feedback(feedback, {"category": "culture", "name": "Unknown"})


@router.get("/recommendations/{user_id}")
async def recommendations(user_id: str, city: str = "nyc", count: int = 5):
    """Get personalized activity recommendations with explanations.

    Uses cosine similarity between the user's preference vector
    and activity category vectors. Each recommendation includes
    a human-readable explanation like 'Recommended because you liked X'.
    """
    city_data = get_city_data(city)
    attractions = city_data.get("attractions", [])

    recs = get_recommendations(user_id, attractions, count)

    return {
        "user_id": user_id,
        "city": city,
        "recommendations": recs,
        "profile": get_profile_summary(user_id),
    }


@router.get("/profile/{user_id}")
async def profile(user_id: str):
    """Get user's current preference profile summary."""
    return get_profile_summary(user_id)
