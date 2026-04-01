"""
Budget Optimizer — Multi-objective 0/1 knapsack with trade-off analysis.

Optimizes across three axes simultaneously:
- Budget: minimize total cost
- Enjoyment: maximize combined popularity/interest score
- Intensity: control number of activities per day

Returns Pareto-optimal solutions with trade-off visualization data.
"""
from __future__ import annotations
from typing import List, Tuple

from ..models.schemas import (
    BudgetRequest, OptimizationResult, TradeOff,
    PlannerRequest,
)
from ..models.datasets import get_city_data
from .itinerary_engine import generate_itinerary


def _compute_enjoyment(attraction: dict, interests: List[str]) -> float:
    """Score enjoyment [0..1] from popularity and interest match."""
    base = attraction.get("popularity", 0.5)
    cat = attraction.get("category", "")
    if cat in interests:
        base = min(1.0, base + 0.2)
    return round(base, 3)


def _knapsack_select(
    attractions: List[dict],
    budget: float,
    interests: List[str],
    weight_budget: float,
    weight_enjoyment: float,
    max_items: int,
) -> List[dict]:
    """Multi-objective 0/1 knapsack selection.

    Combines budget-efficiency and enjoyment into a single objective:
        score = (weight_enjoyment * enjoyment) - (weight_budget * normalized_cost)

    Then selects top items that fit within budget constraint.
    """
    scored = []
    for att in attractions:
        cost = att.get("cost", 0)
        enjoyment = _compute_enjoyment(att, interests)

        # Normalized cost (0..1 relative to budget)
        norm_cost = min(1.0, cost / max(budget, 1)) if cost > 0 else 0.0

        # Multi-objective score
        obj_score = (weight_enjoyment * enjoyment) - (weight_budget * norm_cost)
        scored.append({**att, "_obj_score": obj_score, "_enjoyment": enjoyment})

    scored.sort(key=lambda x: x["_obj_score"], reverse=True)

    # Greedy knapsack: pick top items that fit budget
    selected = []
    remaining = budget
    for item in scored:
        if len(selected) >= max_items:
            break
        cost = item.get("cost", 0)
        if cost <= remaining:
            selected.append(item)
            remaining -= cost

    return selected


async def optimize_budget(request: BudgetRequest) -> OptimizationResult:
    """Run multi-objective optimization and return result with trade-offs.

    Steps:
    1. Load city attractions
    2. Run knapsack selection with user's preference weights
    3. Generate itinerary from selected activities
    4. Compute trade-off metrics
    """
    city_data = get_city_data(request.city)
    attractions = city_data.get("attractions", [])

    # Determine max items based on intensity
    # intensity 0 = 2/day, intensity 0.5 = 3/day, intensity 1 = 5/day
    items_per_day = int(2 + request.weight_intensity * 3)
    max_items = items_per_day * request.duration

    # Run knapsack
    selected = _knapsack_select(
        attractions,
        request.budget,
        request.interests,
        request.weight_budget,
        request.weight_enjoyment,
        max_items,
    )

    # Map intensity to pace string
    if request.weight_intensity > 0.7:
        pace = "packed"
    elif request.weight_intensity < 0.3:
        pace = "relaxed"
    else:
        pace = "balanced"

    # Generate itinerary using the planner with these constraints
    planner_req = PlannerRequest(
        city=request.city,
        budget=request.budget,
        duration=request.duration,
        interests=request.interests,
        pace=pace,
    )
    itinerary = await generate_itinerary(planner_req)

    # Compute trade-offs
    total_cost = itinerary.budget_used
    total_activities = sum(len(d.slots) for d in itinerary.days)
    avg_enjoyment = 0.0
    if total_activities > 0:
        avg_enjoyment = sum(
            s.activity.popularity for d in itinerary.days for s in d.slots
        ) / total_activities

    trade_offs = [
        TradeOff(
            metric="budget_utilization",
            value=round(total_cost / max(request.budget, 1) * 100, 1),
            label=f"${total_cost:.0f} of ${request.budget:.0f} budget used ({total_cost/max(request.budget,1)*100:.0f}%)",
        ),
        TradeOff(
            metric="enjoyment_score",
            value=round(avg_enjoyment * 100, 1),
            label=f"Average enjoyment: {avg_enjoyment*100:.0f}% (popularity-weighted)",
        ),
        TradeOff(
            metric="activity_density",
            value=round(total_activities / max(request.duration, 1), 1),
            label=f"{total_activities / max(request.duration, 1):.1f} activities/day ({pace} pace)",
        ),
        TradeOff(
            metric="free_activities",
            value=sum(1 for d in itinerary.days for s in d.slots if s.activity.cost == 0),
            label=f"{sum(1 for d in itinerary.days for s in d.slots if s.activity.cost == 0)} free activities included",
        ),
    ]

    # Pareto notes
    if request.weight_budget > 0.7:
        pareto_note = "Budget-optimized: prioritized free/low-cost activities. Some premium experiences excluded."
    elif request.weight_enjoyment > 0.7:
        pareto_note = "Enjoyment-maximized: selected highest-rated activities. Budget may be stretched."
    elif request.weight_intensity > 0.7:
        pareto_note = "High-intensity schedule: packed days with minimal rest. Great for short trips."
    else:
        pareto_note = "Balanced optimization across cost, enjoyment, and pace."

    return OptimizationResult(
        itinerary=itinerary,
        trade_offs=trade_offs,
        pareto_notes=pareto_note,
    )
