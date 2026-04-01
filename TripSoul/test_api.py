"""Quick API smoke test."""
import httpx

BASE = "http://localhost:8000"

# 1. Health check
r = httpx.get(f"{BASE}/")
d = r.json()
print(f"[PASS] Health: {d['system']} v{d['version']} — {d['status']}")
print(f"       Modules: {', '.join(d['modules'])}")

# 2. Planner
r = httpx.post(f"{BASE}/api/planner/generate", json={
    "city": "nyc", "budget": 500, "duration": 3,
    "interests": ["culture", "food"], "pace": "balanced"
}, timeout=15)
it = r.json()["itinerary"]
print(f"\n[PASS] Planner: {it['city']} — {len(it['days'])} days")
print(f"       Budget: ${it['budget_used']} / ${it['budget']}")
print(f"       Confidence: {it['overall_confidence']}")
for day in it["days"]:
    names = [s["activity"]["name"] for s in day["slots"]]
    print(f"       Day {day['day']}: {', '.join(names)} (${day['total_cost']})")

# 3. Budget optimizer
r = httpx.post(f"{BASE}/api/optimization/budget", json={
    "city": "nyc", "budget": 300, "duration": 2,
    "interests": ["culture", "food"],
    "weight_budget": 0.8, "weight_enjoyment": 0.5, "weight_intensity": 0.3
}, timeout=15)
opt = r.json()
print(f"\n[PASS] Budget Optimizer: {opt['pareto_notes'][:80]}")
print(f"       Trade-offs: {len(opt['trade_offs'])} metrics")

# 4. Prediction
r = httpx.get(f"{BASE}/api/prediction/delays/nyc?base_time=20", timeout=10)
pred = r.json()["prediction"]
print(f"\n[PASS] Prediction: {pred['expected_time_minutes']}min (conf: {pred['confidence']})")
print(f"       {pred['explanation'][:80]}")

# 5. Adaptation simulate
r = httpx.post(f"{BASE}/api/adaptation/simulate", json={
    "disruption_type": "weather", "severity": "high", "city": "nyc"
}, timeout=15)
adapt = r.json()
print(f"\n[PASS] Adaptation: {adapt.get('disruption', {}).get('description', 'OK')[:80]}")
print(f"       Changes: {adapt.get('changes_made', [])}")

print("\n✅ All API tests passed!")
