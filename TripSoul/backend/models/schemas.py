"""
Pydantic models for TripSoul AI Travel OS.
Every request/response is strictly typed for production-grade reliability.
"""
from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


# ── Planner ──────────────────────────────────────────────────────────────────

class PlannerRequest(BaseModel):
    city: str = Field(..., description="Target city: nyc, tokyo, or paris")
    budget: float = Field(..., gt=0, description="Total trip budget in USD")
    duration: int = Field(..., ge=1, le=14, description="Trip duration in days")
    start_date: str = Field(default="", description="e.g. 2026-05-01")
    end_date: str = Field(default="", description="e.g. 2026-05-04")
    party_size: str = Field(default="couple", description="solo, couple, family, group")
    mood: str = Field(default="relaxed", description="relaxed, energetic, romantic, family")
    dietary_preference: str = Field(default="any", description="any, vegetarian, vegan, halal")
    interests: List[str] = Field(
        default_factory=lambda: ["culture", "food"],
        description="Interest categories: culture, food, adventure, nightlife, nature, shopping, history",
    )
    pace: str = Field(
        default="balanced",
        description="Travel pace: packed, balanced, or relaxed",
    )


class Activity(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lng: float
    cost: float = Field(ge=0)
    duration_hours: float = Field(gt=0)
    popularity: float = Field(ge=0, le=1)
    description: str = ""
    weather_sensitive: bool = False
    opening_hour: int = Field(default=9, ge=0, le=23)
    closing_hour: int = Field(default=18, ge=0, le=23)
    confidence_score: float = Field(default=0.85, ge=0, le=1)
    reason: str = ""
    tags: List[str] = Field(default_factory=list)


class TimeSlot(BaseModel):
    start_time: str  # "09:00"
    end_time: str    # "11:00"
    activity: Activity
    travel_time_minutes: int = 0
    travel_distance_km: float = 0.0
    availability_status: str = "Available"
    surge_multiplier: float = 1.0


class DayPlan(BaseModel):
    day: int
    date_label: str = ""
    slots: List[TimeSlot] = Field(default_factory=list)
    total_cost: float = 0.0
    total_travel_minutes: int = 0


class Itinerary(BaseModel):
    city: str
    duration: int
    budget: float
    budget_used: float = 0.0
    days: List[DayPlan] = Field(default_factory=list)
    overall_confidence: float = 0.85
    reasoning: str = ""


# ── Budget Optimization ──────────────────────────────────────────────────────

class BudgetRequest(BaseModel):
    city: str
    budget: float = Field(gt=0)
    duration: int = Field(ge=1, le=14)
    interests: List[str] = Field(default_factory=lambda: ["culture", "food"])
    weight_budget: float = Field(default=0.5, ge=0, le=1, description="0=ignore cost, 1=minimize cost")
    weight_enjoyment: float = Field(default=0.5, ge=0, le=1, description="0=ignore fun, 1=maximize fun")
    weight_intensity: float = Field(default=0.5, ge=0, le=1, description="0=relaxed, 1=packed schedule")


class TradeOff(BaseModel):
    metric: str
    value: float
    label: str


class OptimizationResult(BaseModel):
    itinerary: Itinerary
    trade_offs: List[TradeOff] = Field(default_factory=list)
    pareto_notes: str = ""


# ── Prediction ───────────────────────────────────────────────────────────────

class PredictionResult(BaseModel):
    location: str
    base_time_minutes: float
    congestion_multiplier: float = 1.0
    weather_impact: float = 1.0
    variability_factor: float = 0.1
    expected_time_minutes: float = 0.0
    confidence: float = Field(ge=0, le=1, default=0.8)
    explanation: str = ""


# ── Adaptation / Disruption ──────────────────────────────────────────────────

class DisruptionEvent(BaseModel):
    type: str  # "weather", "closure", "delay", "congestion"
    severity: str = "medium"  # "low", "medium", "high"
    description: str = ""
    affected_activities: List[str] = Field(default_factory=list)
    timestamp: str = ""


class AdaptationResponse(BaseModel):
    disruption: DisruptionEvent
    original_plan: Optional[Itinerary] = None
    adapted_plan: Optional[Itinerary] = None
    changes_made: List[str] = Field(default_factory=list)
    reasoning: str = ""


# ── Personalization ──────────────────────────────────────────────────────────

class UserFeedback(BaseModel):
    user_id: str = "default"
    activity_id: str
    action: str  # "click", "save", "dwell", "dismiss"
    dwell_seconds: float = 0.0


class PersonalizationResponse(BaseModel):
    user_id: str
    recommendations: List[Activity] = Field(default_factory=list)
    explanations: Dict[str, str] = Field(default_factory=dict)  # activity_id -> explanation


# ── Simulation ───────────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    disruption_type: str = Field(
        default="weather",
        description="Type: weather, closure, delay"
    )
    severity: str = Field(default="medium")
    city: str = Field(default="nyc")
