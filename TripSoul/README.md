# TripSoul — AI Travel Operating System

An intelligent travel OS that autonomously plans, optimizes, and adapts trips in real time using decision intelligence.

## Architecture

```
TripSoul/
├── backend/          FastAPI async backend
│   ├── main.py       App entry + router registration
│   ├── routers/      5 API routers
│   │   ├── planner.py           Itinerary generation
│   │   ├── personalization.py   Cosine similarity recommender
│   │   ├── optimization.py      Multi-objective knapsack
│   │   ├── prediction.py        Delay estimation
│   │   └── adaptation.py        SSE disruption events
│   ├── services/     7 intelligence modules
│   │   ├── itinerary_engine.py  Rule+heuristic optimization
│   │   ├── personalization_engine.py  Preference vectors
│   │   ├── budget_optimizer.py  0/1 knapsack solver
│   │   ├── prediction_service.py Strategy-pattern delays
│   │   ├── adaptation_loop.py   Background poll + SSE
│   │   ├── weather_service.py   OpenWeather + mock
│   │   └── maps_service.py      Google Maps + mock
│   ├── models/       Pydantic schemas + city datasets
│   └── utils/        Helpers + mock data
├── frontend/         Vite + React
│   └── src/
│       ├── App.jsx   Router + global state
│       └── components/
│           ├── Planner.jsx         AI itinerary generator
│           ├── MapView.jsx         Leaflet interactive map
│           ├── Timeline.jsx        Day-by-day schedule
│           ├── BudgetOptimizer.jsx  3-slider optimizer
│           ├── Decisions.jsx       Explanation panel
│           └── DisruptionBanner.jsx Live alerts
└── README.md
```

## Decision Pipeline

```
User Input → Itinerary Engine → Prediction Layer → Budget Optimizer
                                       ↓
                              Adaptation Loop (30s poll)
                                       ↓
                              Disruption detected?
                              ├── YES → Re-optimize → SSE push → UI update
                              └── NO  → Continue monitoring
```

## Quick Start

### Backend

```bash
cd TripSoul/backend
pip install -r requirements.txt
cp .env.example .env        # Add API keys (optional — mocks work without them)
python -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd TripSoul/frontend
npm install
npm run dev                  # http://localhost:5173
```

## Demo Flow

1. **Generate**: Select NYC → $500 budget → 3 days → Generate
2. **Optimize**: Go to Budget tab → move sliders → instant re-optimization
3. **Disrupt**: Go to Decisions tab → click "Simulate Rain" → watch auto-replan
4. **Explore**: Map tab shows pins + routes, Timeline shows day-by-day schedule

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/planner/generate` | POST | Generate structured itinerary |
| `/api/planner/replan` | POST | Re-optimize after disruption |
| `/api/optimization/budget` | POST | Multi-objective budget optimization |
| `/api/personalization/track` | POST | Log user interaction |
| `/api/personalization/recommendations/{id}` | GET | Get personalized recs |
| `/api/prediction/delays/{city}` | GET | Delay estimation |
| `/api/prediction/conditions/{city}` | GET | Weather + congestion analysis |
| `/api/adaptation/status` | GET | Current disruption status |
| `/api/adaptation/events` | GET | SSE live updates |
| `/api/adaptation/simulate` | POST | Trigger simulated disruption |

## Deployment

### Backend → Railway
```bash
# railway.toml
[build]
builder = "NIXPACKS"
[deploy]
startCommand = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
```

### Frontend → Vercel
```bash
cd frontend && npx vercel --prod
# Set VITE_API_URL env var to your Railway backend URL
```

## Cities Available

- **NYC**: 16 attractions (Statue of Liberty, Central Park, MoMA, Broadway...)
- **Tokyo**: 15 attractions (Senso-ji, TeamLab, Shibuya, Tsukiji...)
- **Paris**: 16 attractions (Eiffel Tower, Louvre, Versailles, Catacombs...)

All with real coordinates, costs, categories, popularity weights, and weather sensitivity.
