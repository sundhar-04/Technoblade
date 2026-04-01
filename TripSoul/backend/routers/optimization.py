"""
Optimization Router — Budget optimization with trade-off analysis.
"""
from fastapi import APIRouter
from ..models.schemas import BudgetRequest
from ..services.budget_optimizer import optimize_budget

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


@router.post("/budget")
async def optimize(request: BudgetRequest):
    """Multi-objective budget optimization using knapsack logic.

    User controls three sliders:
    - weight_budget (0..1): 0=ignore cost, 1=minimize cost
    - weight_enjoyment (0..1): 0=ignore fun, 1=maximize fun
    - weight_intensity (0..1): 0=relaxed, 1=packed schedule

    Returns optimized itinerary + trade-off analysis showing
    what you gain and lose with each slider position.
    """
    result = await optimize_budget(request)
    return result.model_dump()
