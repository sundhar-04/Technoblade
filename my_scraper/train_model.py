# ── Step 2: train_model.py ────────────────────────────────────────────────
# Run once after collecting enough rows (50+ is fine for a demo)
# Produces: delay_model.pkl

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

FEATURES = [
    "avg_delay", "max_delay", "route_popularity",
    "time_of_day", "day_of_week", "season", "is_major_station"
]
TARGET = "actual_delay_at_hub"

def train():
    df = pd.read_csv("train_delay_dataset.csv").dropna()
    print(f"Dataset: {len(df)} rows")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    print(f"MAE: {mae:.1f} minutes")  # show this number to judges

    # Feature importance — great to show judges
    for feat, imp in sorted(
        zip(FEATURES, model.feature_importances_),
        key=lambda x: -x[1]
    ):
        print(f"  {feat:<22} {imp:.3f}")

    joblib.dump(model, "delay_model.pkl")
    print("Saved: delay_model.pkl")

if __name__ == "__main__":
    train()