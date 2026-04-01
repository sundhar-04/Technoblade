"""
Prediction Router — Delay estimation with confidence scores.
"""
from fastapi import APIRouter
from ..services.prediction_service import predict_delay, predict_all_slots
from ..services.weather_service import get_weather, weather_impact_factor

router = APIRouter(prefix="/api/prediction", tags=["prediction"])


@router.get("/delays/{city}")
async def get_delays(city: str, base_time: float = 20.0, hour: int | None = None):
    """Get delay estimation for a route in a city.

    Returns:
    - expected_time = base_time + variability_factor * congestion * weather_impact
    - confidence score
    - human-readable explanation

    Architecture allows later ML model upgrade via strategy pattern.
    """
    weather = await get_weather(city)
    w_impact = weather_impact_factor(weather)

    prediction = predict_delay(
        location=f"Central {city.upper()}",
        base_time_minutes=base_time,
        weather_impact=w_impact,
        hour=hour,
    )

    return {
        "prediction": prediction.model_dump(),
        "weather": weather,
    }


@router.get("/conditions/{city}")
async def get_conditions(city: str):
    """Get current weather + congestion impact analysis for a city.

    Combines weather data with congestion patterns to provide
    a comprehensive travel conditions overview.
    """
    weather = await get_weather(city)
    w_impact = weather_impact_factor(weather)

    # Sample predictions for different times of day
    samples = []
    for h in [8, 10, 12, 14, 17, 19, 21]:
        pred = predict_delay(
            location=f"Sample route at {h}:00",
            base_time_minutes=20,
            weather_impact=w_impact,
            hour=h,
        )
        samples.append({
            "hour": h,
            "expected_minutes": pred.expected_time_minutes,
            "congestion": pred.congestion_multiplier,
            "confidence": pred.confidence,
        })

    return {
        "city": city,
        "weather": weather,
        "weather_impact_factor": w_impact,
        "hourly_predictions": samples,
        "summary": (
            f"{'Rainy' if w_impact > 1.1 else 'Clear'} conditions in {city.upper()}. "
            f"Weather adds {(w_impact-1)*100:.0f}% to travel times. "
            f"Rush hours (8-10, 17-19) see highest congestion."
        ),
    }
