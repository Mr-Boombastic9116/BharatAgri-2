"""
Comprehensive Evaluation Script for AI & Optimization Engines in BharatAgri Iteration 2.
Evaluates XGBoost Regressor (MAE, RMSE, R2) and Isolation Forest (Precision, Recall, F1).
Populates ai_model_metrics in MySQL database.
"""

import os
import json
import pymysql
from ml.training.train_supply_model import train_supply_model
from ml.training.train_anomaly_model import train_anomaly_model

def run_evaluation():
    print("=" * 60)
    print("BHARATAGRI ITERATION 2 - AI MODEL EVALUATION REPORT")
    print("Dataset: Synthetic demonstration dataset (Seed: 42)")
    print("Notice: Synthetic evaluation metrics represent benchmark validation.")
    print("=" * 60)

    supply_metrics = train_supply_model()
    anomaly_metrics = train_anomaly_model()

    print("\n--- Summary of Model Metrics ---")
    print("1. XGBoost Supply Forecaster:")
    print(f"   MAE:  {supply_metrics['mae']} Quintals")
    print(f"   RMSE: {supply_metrics['rmse']} Quintals")
    print(f"   R²:   {supply_metrics['r2_score']}")

    print("\n2. Isolation Forest Procurement Anomaly Detector:")
    print(f"   Precision: {anomaly_metrics['precision_score']}")
    print(f"   Recall:    {anomaly_metrics['recall_score']}")
    print(f"   F1-Score:  {anomaly_metrics['f1_score']}")
    print(f"   Outliers:  {anomaly_metrics['outliers_flagged']} cases flagged")

    # Connect to MySQL and record metrics if available
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", 3306))
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "bharatagri_iteration2")

    try:
        conn = pymysql.connect(host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name)
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM ai_model_metrics WHERE model_name IN (%s, %s)",
                           (supply_metrics['model_name'], anomaly_metrics['model_name']))
            
            cursor.execute("""
                INSERT INTO ai_model_metrics (model_name, model_type, mae, rmse, r2_score, dataset_info)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (supply_metrics['model_name'], supply_metrics['model_type'],
                  supply_metrics['mae'], supply_metrics['rmse'], supply_metrics['r2_score'], supply_metrics['dataset_info']))

            cursor.execute("""
                INSERT INTO ai_model_metrics (model_name, model_type, precision_score, recall_score, f1_score, dataset_info)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (anomaly_metrics['model_name'], anomaly_metrics['model_type'],
                  anomaly_metrics['precision_score'], anomaly_metrics['recall_score'], anomaly_metrics['f1_score'], anomaly_metrics['dataset_info']))

        conn.commit()
        conn.close()
        print("\nSuccessfully updated `ai_model_metrics` table in MySQL database.")
    except Exception as e:
        print(f"\n[Note] Could not persist metrics to MySQL: {e}")

    return {
        "supply_metrics": supply_metrics,
        "anomaly_metrics": anomaly_metrics
    }

if __name__ == "__main__":
    run_evaluation()
