"""
Prediction Service — Delay estimation with congestion and weather factors.

Formula: expected_time = base_time * (1 + variability_factor) * congestion_multiplier * weather_impact

Architecture uses strategy pattern for future ML model drop-in:
- PredictionStrategy (base class)
- HeuristicPredictor (current: rule-based)
- MLPredictor (future: trained model)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime

from ..models.schemas import PredictionResult
from ..utils.mock_data import get_mock_congestion


class PredictionStrategy(ABC):
    """Base class for prediction strategies. Swap in ML models later."""

    @abstractmethod
    def predict(
        self,
        base_time_minutes: float,
        congestion: float,
        weather_impact: float,
        hour: int,
    ) -> PredictionResult:
        pass


class HeuristicPredictor(PredictionStrategy):
    """Rule-based predictor using congestion multiplier and weather impact.

    expected_time = base_time * (1 + variability) * congestion * weather_impact

    Confidence decreases with:
    - Higher variability
    - Rush hour times
    - Bad weather
    """

    def predict(
        self,
        base_time_minutes: float,
        congestion: float,
        weather_impact: float,
        hour: int,
    ) -> PredictionResult:
        # Variability: higher during rush hours
        if 8 <= hour <= 10 or 17 <= hour <= 19:
            variability = 0.25
        elif 11 <= hour <= 16:
            variability = 0.15
        else:
            variability = 0.10

        expected = base_time_minutes * (1 + variability) * congestion * weather_impact

        # Confidence: lower when more uncertain
        confidence = 0.95
        if variability > 0.2:
            confidence -= 0.10
        if congestion > 1.3:
            confidence -= 0.10
        if weather_impact > 1.2:
            confidence -= 0.10
        confidence = max(0.5, confidence)

        explanation = self._explain(
            base_time_minutes, expected, congestion, weather_impact, variability, hour
        )

        return PredictionResult(
            location="",  # Filled by caller
            base_time_minutes=base_time_minutes,
            congestion_multiplier=round(congestion, 2),
            weather_impact=round(weather_impact, 2),
            variability_factor=variability,
            expected_time_minutes=round(expected, 1),
            confidence=round(confidence, 2),
            explanation=explanation,
        )

    def _explain(
        self, base: float, expected: float,
        congestion: float, weather: float,
        variability: float, hour: int,
    ) -> str:
        parts = [f"Base transit time: {base:.0f} min"]

        if congestion > 1.2:
            parts.append(f"congestion adds {(congestion-1)*100:.0f}%")
        if weather > 1.1:
            parts.append(f"weather conditions add {(weather-1)*100:.0f}%")
        if variability > 0.15:
            parts.append(f"rush hour variability: ±{variability*100:.0f}%")

        added = expected - base
        parts.append(f"Expected: {expected:.0f} min (+{added:.0f} min)")

        return " → ".join(parts)


# Default predictor instance
_predictor: PredictionStrategy = HeuristicPredictor()


def set_predictor(predictor: PredictionStrategy):
    """Swap in a different prediction strategy (e.g., trained ML model)."""
    global _predictor
    _predictor = predictor


def predict_delay(
    location: str,
    base_time_minutes: float,
    weather_impact: float = 1.0,
    hour: int | None = None,
) -> PredictionResult:
    """Predict expected travel time with delay estimation.

    Args:
        location: Route or location name
        base_time_minutes: Normal travel time without delays
        weather_impact: Multiplier from weather service [1.0..1.5]
        hour: Hour of day (0-23). Defaults to current hour.
    """
    if hour is None:
        hour = datetime.now().hour

    congestion = get_mock_congestion(hour)
    result = _predictor.predict(base_time_minutes, congestion, weather_impact, hour)
    result.location = location
    return result


def predict_all_slots(
    slots: list,
    weather_impact: float = 1.0,
) -> List[PredictionResult]:
    """Predict delays for all time slots in an itinerary day."""
    predictions = []
    for slot in slots:
        if slot.travel_time_minutes > 0:
            hour = int(slot.start_time.split(":")[0])
            pred = predict_delay(
                location=f"→ {slot.activity.name}",
                base_time_minutes=slot.travel_time_minutes,
                weather_impact=weather_impact,
                hour=hour,
            )
            predictions.append(pred)
    return predictions
