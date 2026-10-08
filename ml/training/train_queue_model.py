import pandas as pd
import numpy as np
import os
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

excel_path = 'data/raw/SIH_26032_KisanFlow_Synthetic_Data.xlsx'
df = pd.read_excel(excel_path, sheet_name='ml_training_dataset')

feature_cols = [
    'queue_before',
    'active_weighing_machines',
    'staff_available',
    'equipment_failure_flag',
    'weather_delay_flag',
    'travel_distance_km',
    'historical_avg_processing_min',
    'hour',
    'day_of_week',
    'is_peak_hour'
]

X = df[feature_cols].copy()
y = df['actual_wait_min'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 1. Baseline Queueing Model: (queue_before * historical_avg_processing_min) / active_weighing_machines
baseline_pred = (X_test['queue_before'] * X_test['historical_avg_processing_min']) / np.maximum(X_test['active_weighing_machines'], 1)
# Adjust for equipment failure and weather delay if applicable
baseline_mae = mean_absolute_error(y_test, baseline_pred)
baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
baseline_r2 = r2_score(y_test, baseline_pred)

print(f"--- Baseline Queueing Model ---")
print(f"MAE: {baseline_mae:.2f} min, RMSE: {baseline_rmse:.2f} min, R2: {baseline_r2:.4f}")

# 2. Random Forest Regressor
rf = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_mae = mean_absolute_error(y_test, rf_pred)
rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
rf_r2 = r2_score(y_test, rf_pred)

print(f"\n--- Random Forest Regressor ---")
print(f"MAE: {rf_mae:.2f} min, RMSE: {rf_rmse:.2f} min, R2: {rf_r2:.4f}")

# 3. Gradient Boosting Regressor
gb = GradientBoostingRegressor(n_estimators=150, learning_rate=0.08, max_depth=5, random_state=42)
gb.fit(X_train, y_train)
gb_pred = gb.predict(X_test)
gb_mae = mean_absolute_error(y_test, gb_pred)
gb_rmse = np.sqrt(mean_squared_error(y_test, gb_pred))
gb_r2 = r2_score(y_test, gb_pred)

print(f"\n--- Gradient Boosting Regressor ---")
print(f"MAE: {gb_mae:.2f} min, RMSE: {gb_rmse:.2f} min, R2: {gb_r2:.4f}")

# 4. XGBoost Regressor
xgb_model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, n_jobs=-1)
xgb_model.fit(X_train, y_train)
xgb_pred = xgb_model.predict(X_test)
xgb_mae = mean_absolute_error(y_test, xgb_pred)
xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb_pred))
xgb_r2 = r2_score(y_test, xgb_pred)

print(f"\n--- XGBoost Regressor ---")
print(f"MAE: {xgb_mae:.2f} min, RMSE: {xgb_rmse:.2f} min, R2: {xgb_r2:.4f}")

# Select best model
models = {
    'baseline': (baseline_mae, baseline_rmse, baseline_r2),
    'random_forest': (rf_mae, rf_rmse, rf_r2),
    'gradient_boosting': (gb_mae, gb_rmse, gb_r2),
    'xgboost': (xgb_mae, xgb_rmse, xgb_r2)
}

best_model_name = min(['random_forest', 'gradient_boosting', 'xgboost'], key=lambda k: models[k][0])
print(f"\nBest Model: {best_model_name} (MAE: {models[best_model_name][0]:.2f} min)")

# Save the best model
os.makedirs('ml/models', exist_ok=True)
best_model = xgb_model if best_model_name == 'xgboost' else (rf if best_model_name == 'random_forest' else gb)
model_path = 'ml/models/queue_wait_model.joblib'
joblib.dump(best_model, model_path)
print(f"Saved best model to {model_path}")

# Feature importances
importances = best_model.feature_importances_
feat_imp = {feat: float(imp) for feat, imp in zip(feature_cols, importances)}

metrics = {
    "comparison": {
        "baseline_queueing_model": {
            "mae_min": round(baseline_mae, 2),
            "rmse_min": round(baseline_rmse, 2),
            "r2_score": round(baseline_r2, 4),
            "description": "Deterministic Little's Law approximation: (queue_before * historical_avg_processing_min) / active_weighing_machines"
        },
        "random_forest": {
            "mae_min": round(rf_mae, 2),
            "rmse_min": round(rf_rmse, 2),
            "r2_score": round(rf_r2, 4)
        },
        "gradient_boosting": {
            "mae_min": round(gb_mae, 2),
            "rmse_min": round(gb_rmse, 2),
            "r2_score": round(gb_r2, 4)
        },
        "xgboost": {
            "mae_min": round(xgb_mae, 2),
            "rmse_min": round(xgb_rmse, 2),
            "r2_score": round(xgb_r2, 4)
        }
    },
    "best_model": best_model_name,
    "feature_columns": feature_cols,
    "feature_importances": feat_imp,
    "sample_count": len(df),
    "test_sample_count": len(X_test),
    "residual_std": float(np.std(y_test - best_model.predict(X_test)))
}

metrics_path = 'ml/models/queue_metrics.json'
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"Saved metrics to {metrics_path}")
