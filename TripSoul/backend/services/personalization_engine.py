"""
Personalization Engine — Cosine similarity recommender with implicit feedback tracking.

Tracks user interactions (clicks, saves, dwell time) to build preference vectors.
Uses cosine similarity to score activities and generate explanations.
"""
from __future__ import annotations
import math
from typing import Dict, List
from collections import defaultdict

from ..models.schemas import Activity, UserFeedback

# Category dimensions for preference vectors
CATEGORIES = ["culture", "food", "adventure", "nightlife", "nature", "shopping", "history"]

# In-memory user profiles (production would use a database)
_user_profiles: Dict[str, Dict] = {}


def _get_or_create_profile(user_id: str) -> dict:
    """Get or initialize a user preference profile."""
    if user_id not in _user_profiles:
        _user_profiles[user_id] = {
            "preference_vector": {cat: 0.5 for cat in CATEGORIES},  # Neutral start
            "interaction_count": 0,
            "liked_activities": [],   # Activity IDs the user saved/clicked
            "liked_names": [],        # Activity names for explanations
            "category_scores": defaultdict(float),
        }
    return _user_profiles[user_id]


def track_feedback(feedback: UserFeedback, activity: dict) -> dict:
    """Process implicit feedback and update user preference vector.

    Actions and their weight:
    - click: +0.1 to category
    - save: +0.3 to category
    - dwell: +0.01 per second (capped at +0.3)
    - dismiss: -0.15 from category
    """
    profile = _get_or_create_profile(feedback.user_id)
    category = activity.get("category", "culture")
    vec = profile["preference_vector"]

    weight = 0.0
    if feedback.action == "click":
        weight = 0.1
    elif feedback.action == "save":
        weight = 0.3
        if feedback.activity_id not in profile["liked_activities"]:
            profile["liked_activities"].append(feedback.activity_id)
            profile["liked_names"].append(activity.get("name", ""))
    elif feedback.action == "dwell":
        weight = min(0.3, feedback.dwell_seconds * 0.01)
    elif feedback.action == "dismiss":
        weight = -0.15

    # Update preference vector
    if category in vec:
        vec[category] = max(0.0, min(1.0, vec[category] + weight))

    profile["interaction_count"] += 1
    profile["category_scores"][category] += weight

    return {"updated": True, "profile_summary": _summarize_profile(profile)}


def get_recommendations(
    user_id: str,
    attractions: List[dict],
    count: int = 5,
) -> List[dict]:
    """Score and rank activities using cosine similarity against user preference vector."""
    profile = _get_or_create_profile(user_id)
    user_vec = profile["preference_vector"]

    scored = []
    for att in attractions:
        # Build activity vector (1.0 in its category, 0 elsewhere)
        att_vec = {cat: 0.0 for cat in CATEGORIES}
        cat = att.get("category", "culture")
        if cat in att_vec:
            att_vec[cat] = 1.0

        # Also factor in popularity
        if cat in att_vec:
            att_vec[cat] *= att.get("popularity", 0.5)

        similarity = _cosine_similarity(user_vec, att_vec)
        explanation = _generate_explanation(att, profile, similarity)

        scored.append({
            **att,
            "personalization_score": round(similarity, 3),
            "explanation": explanation,
        })

    scored.sort(key=lambda x: x["personalization_score"], reverse=True)
    return scored[:count]


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two category vectors."""
    keys = set(vec_a.keys()) | set(vec_b.keys())
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in keys)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _generate_explanation(activity: dict, profile: dict, score: float) -> str:
    """Generate human-readable explanation for a recommendation."""
    cat = activity.get("category", "culture")
    name = activity.get("name", "")
    liked_names = profile.get("liked_names", [])

    # Find which liked activities share the same category
    similar_liked = [n for n, aid in zip(liked_names, profile.get("liked_activities", []))
                     if aid != activity.get("id")]

    if similar_liked:
        ref = similar_liked[-1]  # Most recent similar activity
        return f"Recommended because you liked {ref}. Both are {cat} experiences."
    elif profile["interaction_count"] > 0:
        pref = profile["preference_vector"]
        top_cat = max(pref, key=pref.get)
        if cat == top_cat:
            return f"Recommended because {cat} is your top interest based on browsing patterns."
        return f"Suggested as a {cat} experience to diversify your itinerary."
    else:
        pop = activity.get("popularity", 0.5)
        if pop > 0.9:
            return f"Highly popular {cat} attraction — a must-see for first-time visitors."
        return f"A notable {cat} experience in this city."


def _summarize_profile(profile: dict) -> dict:
    """Return a summary of user preferences for API response."""
    vec = profile["preference_vector"]
    sorted_prefs = sorted(vec.items(), key=lambda x: x[1], reverse=True)
    return {
        "top_interests": [k for k, v in sorted_prefs[:3]],
        "interaction_count": profile["interaction_count"],
        "preference_vector": vec,
    }


def get_profile_summary(user_id: str) -> dict:
    """Get a user's current preference summary."""
    profile = _get_or_create_profile(user_id)
    return _summarize_profile(profile)
