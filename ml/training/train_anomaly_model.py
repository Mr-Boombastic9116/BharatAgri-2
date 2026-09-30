"""
Training script for Isolation Forest Anomaly Detection Model across procurement transactions.
Evaluates Precision, Recall, and F1 on synthetic demonstration benchmark.
Saves model bundle to ml/models/anomaly_detector_iforest.joblib.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score

def train_anomaly_model():
    print("=== Training Isolation Forest Anomaly Detection Model ===")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_path = os.path.join(base_dir, "ml", "data", "anomaly_training_data.csv")
    model_dir = os.path.join(base_dir, "ml", "models")
    os.makedirs(model_dir, exist_ok=True)

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Anomaly training data not found at: {data_path}. Run generate_data.py first.")

    df = pd.read_csv(data_path)
    print(f"Loaded anomaly dataset: {len(df)} rows, anomaly proportion: {df['is_anomaly'].mean():.2%}")

    feature_cols = [
        "booked_quantity", "collected_quantity", "weighed_quantity",
        "procured_quantity", "moisture_content", "processing_time_mins",
        "qty_difference"
    ]

    X = df[feature_cols].values
    y_true = df["is_anomaly"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y_true, test_size=0.2, random_state=42, stratify=y_true)

    # Contamination set to match expected operational outlier rate ~5%
    model = IsolationForest(
        n_estimators=150,
        contamination=0.06,
        random_state=42,
        max_samples="auto"
    )

    print("Fitting Isolation Forest model...")
    model.fit(X_train)

    # In IsolationForest, -1 indicates outlier, 1 indicates inlier
    raw_preds = model.predict(X_test)
    y_pred = (raw_preds == -1).astype(int)

    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    detected_count = int(np.sum(y_pred == 1))

    print(f"Evaluation Results on Synthetic Ground-Truth Holdout:")
    print(f" - Precision: {precision:.4f}")
    print(f" - Recall:    {recall:.4f}")
    print(f" - F1 Score:  {f1:.4f}")
    print(f" - Outliers flagged: {detected_count} of {len(X_test)} test cases")

    metrics = {
        "model_name": "Isolation Forest Procurement Anomaly Detector",
        "model_type": "ANOMALY_DETECTION",
        "precision_score": round(precision, 4),
        "recall_score": round(recall, 4),
        "f1_score": round(f1, 4),
        "outliers_flagged": detected_count,
        "dataset_info": "Synthetic demonstration dataset (Seed 42)",
        "feature_cols": feature_cols
    }

    bundle = {
        "model": model,
        "feature_cols": feature_cols,
        "metrics": metrics
    }

    model_path = os.path.join(model_dir, "anomaly_detector_iforest.joblib")
    joblib.dump(bundle, model_path)
    print(f"Model bundle saved to: {model_path}")

    metrics_path = os.path.join(model_dir, "anomaly_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics

if __name__ == "__main__":
    train_anomaly_model()
