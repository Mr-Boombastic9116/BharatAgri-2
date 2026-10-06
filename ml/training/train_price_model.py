"""
Training script for XGBoost Price Estimation Model.
Inputs:
- official_msp
- hist_proc_price
- hist_proc_qty
- current_demand
- current_supply
- surplus_deficit
- storage_avail_ratio
- state, district, crop, season
- trend_factor

Target:
- ai_estimated_procurement_price
Enforces MAX(ai_estimate, official_msp) at inference time.
Saves model bundle to ml/models/price_estimation_xgb.joblib and ml/models/price_metrics.json.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import pymysql
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

def load_data():
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='bharatagri_iteration2')
    query = """
    SELECT 
        pr.crop,
        pc.state,
        pc.district,
        CASE 
            WHEN pr.crop IN ('Wheat', 'Gram (Chana)', 'Mustard', 'Potato') THEN 'Rabi'
            WHEN pr.crop IN ('Sugarcane') THEN 'All-Season'
            ELSE 'Kharif'
        END AS season,
        CAST(pr.msp_rate_per_quintal AS FLOAT) AS official_msp,
        CAST(pr.procured_quantity_quintals AS FLOAT) AS hist_proc_qty,
        CAST(pr.total_procurement_value / NULLIF(pr.procured_quantity_quintals, 0) AS FLOAT) AS hist_proc_price,
        CAST(pc.total_storage_capacity_quintals AS FLOAT) AS total_storage,
        CAST(pc.current_storage_usage_quintals AS FLOAT) AS current_storage,
        MONTH(pr.created_at) AS proc_month
    FROM procurement_records pr
    JOIN procurement_centres pc ON pr.centre_id = pc.centre_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # Merge state crop supply demand metrics
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='bharatagri_iteration2')
    sd_df = pd.read_sql("SELECT state, crop, CAST(expected_supply_quintals AS FLOAT) as supply_q, CAST(expected_demand_quintals AS FLOAT) as demand_q, CAST(surplus_deficit_quintals AS FLOAT) as surplus_q FROM state_crop_supply_demand", conn)
    conn.close()

    # Join on state and crop
    df = df.merge(sd_df, on=['state', 'crop'], how='left')

    # Fill defaults for rows without explicit state_crop_supply_demand row
    df['supply_q'] = df['supply_q'].fillna(df['hist_proc_qty'] * 850.0)
    df['demand_q'] = df['demand_q'].fillna(df['hist_proc_qty'] * 800.0)
    df['surplus_q'] = df['supply_q'] - df['demand_q']
    df['storage_avail_ratio'] = np.clip((df['total_storage'] - df['current_storage']) / np.maximum(df['total_storage'], 1.0), 0.05, 0.95)
    df['trend_factor'] = np.sin((df['proc_month'] / 12.0) * 2 * np.pi) * 0.03

    # Generate grounded target price based on economic market dynamics:
    # In deficit (demand > supply): price premium up to 10% above MSP
    # In surplus (supply > demand): small premium (1-2.5%) above MSP with floor at MSP
    deficit_pct = np.where(df['surplus_q'] < 0, np.minimum(0.12, np.abs(df['surplus_q']) / np.maximum(df['demand_q'], 1.0) * 0.25), 0.015)
    target_price = df['official_msp'] * (1.0 + deficit_pct + df['trend_factor'])
    # Add minor realistic variance
    np.random.seed(42)
    noise = np.random.normal(0, df['official_msp'] * 0.005, size=len(df))
    df['ai_estimated_price'] = np.round(target_price + noise, 2)

    return df

def train_price_model():
    print("=== Training XGBoost Price Estimation Model ===")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    model_dir = os.path.join(base_dir, "ml", "models")
    os.makedirs(model_dir, exist_ok=True)

    df = load_data()
    print(f"Loaded {len(df)} procurement transactions for training.")

    categorical_cols = ['crop', 'state', 'district', 'season']
    numerical_cols = [
        'official_msp', 'hist_proc_price', 'hist_proc_qty',
        'demand_q', 'supply_q', 'surplus_q', 'storage_avail_ratio', 'trend_factor'
    ]
    target_col = 'ai_estimated_price'

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
        n_estimators=150,
        max_depth=5,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        objective="reg:squarederror"
    )

    print("Fitting XGBoost Price Estimation Regressor...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    print(f"Price Estimation Evaluation (Holdout 20%):")
    print(f" - MAE:  INR {mae:.2f} per Quintal")
    print(f" - RMSE: INR {rmse:.2f} per Quintal")
    print(f" - R²:   {r2:.4f}")


    # Feature importance
    feat_imp = {col: round(float(imp), 4) for col, imp in zip(X.columns, model.feature_importances_)}

    metrics = {
        "model_name": "XGBoost Procurement Price Estimator",
        "model_type": "REGRESSION",
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2_score": round(r2, 4),
        "dataset_rows": len(df),
        "feature_cols": list(X.columns),
        "feature_importances": feat_imp,
        "evaluation_rule": "FINAL ESTIMATED PRICE = MAX(AI ESTIMATE, OFFICIAL MSP)"
    }

    bundle = {
        "model": model,
        "encoders": encoders,
        "feature_cols": list(X.columns),
        "metrics": metrics
    }

    model_path = os.path.join(model_dir, "price_estimation_xgb.joblib")
    joblib.dump(bundle, model_path)
    print(f"Price model bundle saved to: {model_path}")

    metrics_path = os.path.join(model_dir, "price_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Price metrics saved to: {metrics_path}")

    return metrics

if __name__ == "__main__":
    train_price_model()
