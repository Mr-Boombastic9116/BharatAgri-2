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

    # Chronological Split (Section 7):
    # Historical procurement up to Q3 (Months 1-9) vs peak arrival/holdout (Months 10-12)
    train_mask = df["month"] <= 9
    test_mask = df["month"] > 9

    X_train = X[train_mask]
    y_train = y[train_mask]
    X_test = X[test_mask]
    y_test = y[test_mask]

    # Baseline 1: Historical Mean Baseline
    hist_mean = float(y_train.mean())
    pred_hist = np.full_like(y_test, hist_mean)
    mae_hist = float(mean_absolute_error(y_test, pred_hist))
    rmse_hist = float(np.sqrt(mean_squared_error(y_test, pred_hist)))
    r2_hist = float(r2_score(y_test, pred_hist))

    # Baseline 2: Seasonal Crop Historical Average Baseline
    train_df = df[train_mask]
    test_df = df[test_mask]
    crop_means = train_df.groupby("crop")["procured_quantity"].mean().to_dict()
    pred_seasonal = test_df["crop"].map(crop_means).fillna(hist_mean).values
    mae_season = float(mean_absolute_error(y_test, pred_seasonal))
    rmse_season = float(np.sqrt(mean_squared_error(y_test, pred_seasonal)))
    r2_season = float(r2_score(y_test, pred_seasonal))

    # Baseline 3: Linear Alternative (Ridge Regression)
    from sklearn.linear_model import Ridge
    ridge = Ridge()
    ridge.fit(X_train, y_train)
    pred_ridge = ridge.predict(X_test)
    mae_ridge = float(mean_absolute_error(y_test, pred_ridge))
    rmse_ridge = float(np.sqrt(mean_squared_error(y_test, pred_ridge)))
    r2_ridge = float(r2_score(y_test, pred_ridge))

    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        objective="reg:squarederror"
    )

    print("Fitting XGBoost regressor on chronological training split...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"\nChronological Holdout Evaluation (Months 10-12, {len(X_test)} rows):")
    print(f" - Baseline 1 (Historical Mean):   MAE={mae_hist:.2f} Q, RMSE={rmse_hist:.2f} Q, R²={r2_hist:.4f}")
    print(f" - Baseline 2 (Seasonal Crop Avg): MAE={mae_season:.2f} Q, RMSE={rmse_season:.2f} Q, R²={r2_season:.4f}")
    print(f" - Baseline 3 (Ridge Linear):      MAE={mae_ridge:.2f} Q, RMSE={rmse_ridge:.2f} Q, R²={r2_ridge:.4f}")
    print(f" - XGBoost Supply Forecaster:      MAE={mae:.2f} Q, RMSE={rmse:.2f} Q, R²={r2:.4f}")

    metrics = {
        "model_name": "XGBoost Supply Forecaster",
        "model_type": "REGRESSION",
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2_score": round(r2, 4),
        "dataset_info": "Chronological split (Months 1-9 Train, Months 10-12 Test)",
        "feature_cols": list(X.columns),
        "baselines": {
            "historical_mean": {"mae": round(mae_hist, 4), "rmse": round(rmse_hist, 4), "r2_score": round(r2_hist, 4)},
            "seasonal_crop_average": {"mae": round(mae_season, 4), "rmse": round(rmse_season, 4), "r2_score": round(r2_season, 4)},
            "linear_ridge": {"mae": round(mae_ridge, 4), "rmse": round(rmse_ridge, 4), "r2_score": round(r2_ridge, 4)},
            "xgboost": {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2_score": round(r2, 4)}
        }
    }

    bundle = {
        "model": model,
        "encoders": encoders,
        "feature_cols": list(X.columns),
        "metrics": metrics
    }

    model_path = os.path.join(model_dir, "supply_forecast_xgb.joblib")
    joblib.dump(bundle, model_path)
    print(f"\nModel bundle saved to: {model_path}")

    metrics_path = os.path.join(model_dir, "supply_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics

if __name__ == "__main__":
    train_supply_model()
