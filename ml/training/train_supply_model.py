"""
Training script for XGBoost Supply / Procurement Forecasting Model.
Evaluates MAE, RMSE, and R2 on a synthetic holdout set.
Saves model bundle to ml/models/supply_forecast_xgb.joblib.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

def train_supply_model():
    print("=== Training XGBoost Supply Forecast Model ===")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_path = os.path.join(base_dir, "ml", "data", "procurement_training_data.csv")
    model_dir = os.path.join(base_dir, "ml", "models")
    os.makedirs(model_dir, exist_ok=True)

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Training data not found at: {data_path}. Run generate_data.py first.")

    df = pd.read_csv(data_path)
    print(f"Loaded dataset: {len(df)} rows, columns: {list(df.columns)}")

    categorical_cols = ["centre_id", "state", "district", "crop"]
    numerical_cols = [
        "month", "day_of_week", "registered_farmers_count", "booked_quantity",
        "expected_harvest_quantity", "daily_capacity", "historic_arrival_qty",
        "trucks_demand", "bardan_bags_consumed"
    ]
    target_col = "procured_quantity"

    encoders = {}
    X = pd.DataFrame()
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    for col in numerical_cols:
        X[col] = df[col].astype(float)

    y = df[target_col].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        objective="reg:squarederror"
    )

    print("Fitting XGBoost regressor...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"Evaluation Results (Holdout 20%):")
    print(f" - MAE:  {mae:.4f} Quintals")
    print(f" - RMSE: {rmse:.4f} Quintals")
    print(f" - R²:   {r2:.4f}")

    metrics = {
        "model_name": "XGBoost Supply Forecaster",
        "model_type": "REGRESSION",
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2_score": round(r2, 4),
        "dataset_info": "Synthetic demonstration dataset (Seed 42)",
        "feature_cols": list(X.columns)
    }

    bundle = {
        "model": model,
        "encoders": encoders,
        "feature_cols": list(X.columns),
        "metrics": metrics
    }

    model_path = os.path.join(model_dir, "supply_forecast_xgb.joblib")
    joblib.dump(bundle, model_path)
    print(f"Model bundle saved to: {model_path}")

    metrics_path = os.path.join(model_dir, "supply_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics

if __name__ == "__main__":
    train_supply_model()
