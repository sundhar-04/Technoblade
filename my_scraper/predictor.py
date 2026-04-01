# ── Step 3: predictor.py ──────────────────────────────────────────────────
# Replaces: get_avg_delay_at() in your existing scraper
# Drop-in: same inputs, but prediction instead of lookup

import joblib
import numpy as np
from datetime import datetime
import os

# Try to import the new engine
try:
    from connecting_trains import ConnectionEngine
except ImportError:
    ConnectionEngine = None

_engine = None

def load_engine():
    global _engine
    if _engine is None and ConnectionEngine:
        try:
            # Silence the training output if it happens
            import sys
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            _engine = ConnectionEngine()
            sys.stdout = old_stdout
            print("[ML] Connection Engine loaded (Gradient Boosting)")
        except Exception as e:
            print(f"[ML] Failed to load Connection Engine: {e}")
    return _engine

_legacy_model = None
def load_legacy_model():
    global _legacy_model
    if _legacy_model is None:
        try:
            _legacy_model = joblib.load("delay_model.pkl")
            print("[ML] Legacy model loaded (Random Forest)")
        except FileNotFoundError:
            pass
    return _legacy_model

def predict_delay(avg_delay, max_delay, route_popularity,
                  dep_time_str, is_major_station, train_info=None):
    """
    Unified predictor. 
    If train_info is provided, uses the advanced ConnectionEngine.
    Otherwise falls back to legacy model or statistical baseline.
    """
    engine = load_engine()
    
    # 1. Try advanced ConnectionEngine if we have enough info
    if engine and train_info and 'train_name' in train_info:
        # Map scraper info to engine format if needed
        # scraper 'dep' = '06:00', engine needs 'scheduled_hour' = 6.0
        if 'scheduled_hour' not in train_info and 'dep' in train_info:
            try:
                h, m = map(int, train_info['dep'].split(':'))
                train_info['scheduled_hour'] = h + m/60.0
            except: 
                train_info['scheduled_hour'] = 10.0
        
        # Ensure other fields exist
        train_info.setdefault('avg_delay_min', avg_delay)
        train_info.setdefault('distance_km', 500) # Fallback distance
        train_info.setdefault('frequency', 'Daily')
        
        return engine.predict_delay(train_info)

    # 2. Try legacy model
    model = load_legacy_model()
    if model:
        h = int(dep_time_str.split(':')[0])
        time_of_day  = 0 if 5 <= h < 12 else (1 if h < 18 else 2)
        day_of_week  = datetime.now().weekday()
        month        = datetime.now().month
        season       = 0 if month in [3,4,5] else (1 if month in [6,7,8,9] else 2)

        features = [[
            avg_delay, max_delay, route_popularity,
            time_of_day, day_of_week, season, int(is_major_station)
        ]]
        return round(model.predict(features)[0])

    # 3. Final Fallback: statistical baseline
    std_estimate = (max_delay - avg_delay) / 2
    return round(avg_delay + std_estimate * 0.5)