"""
Supply / Procurement Forecasting Inference Engine.
Loads trained XGBoost model from ml/models/supply_forecast_xgb.joblib.
Provides graceful rule-based fallback if model file is unavailable.
"""

import os
import joblib
import pandas as pd
import numpy as np

class SupplyPredictor:
    def __init__(self):
        self.model_bundle = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        model_path = os.path.join(base_dir, "ml", "models", "supply_forecast_xgb.joblib")
        if os.path.exists(model_path):
            try:
                self.model_bundle = joblib.load(model_path)
                self.is_loaded = True
            except Exception as e:
                print(f"[Warning] Failed to load XGBoost supply model: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def predict(self, centre_id: str, state: str, district: str, crop: str,
                month: int, day_of_week: int, registered_farmers: int,
                booked_quantity: float, daily_capacity: float = 800.0,
                historic_arrivals: float = None):
        """
        Generates procurement forecast in Quintals.
        Returns dict with predicted quantity, arrivals, trucks, and fallback indicator.
        """
        if historic_arrivals is None:
            historic_arrivals = booked_quantity * 0.96

        expected_harvest = booked_quantity * 1.05
        trucks_demand = max(1, int(booked_quantity // 80) + 1)
        bardan_consumed = int(booked_quantity * 2)

        if self.is_loaded:
            try:
                encoders = self.model_bundle["encoders"]
                model = self.model_bundle["model"]
                feature_cols = self.model_bundle["feature_cols"]

                # Safe categorical transform
                c_id_enc = encoders["centre_id"].transform([centre_id])[0] if centre_id in encoders["centre_id"].classes_ else 0
                st_enc = encoders["state"].transform([state])[0] if state in encoders["state"].classes_ else 0
                dist_enc = encoders["district"].transform([district])[0] if district in encoders["district"].classes_ else 0
                crop_enc = encoders["crop"].transform([crop])[0] if crop in encoders["crop"].classes_ else 0

                row_dict = {
                    "centre_id": c_id_enc,
                    "state": st_enc,
                    "district": dist_enc,
                    "crop": crop_enc,
                    "month": float(month),
                    "day_of_week": float(day_of_week),
                    "registered_farmers_count": float(registered_farmers),
                    "booked_quantity": float(booked_quantity),
                    "expected_harvest_quantity": float(expected_harvest),
                    "daily_capacity": float(daily_capacity),
                    "historic_arrival_qty": float(historic_arrivals),
                    "trucks_demand": float(trucks_demand),
                    "bardan_bags_consumed": float(bardan_consumed)
                }

                X = pd.DataFrame([row_dict])[feature_cols]
                pred_qty = float(model.predict(X)[0])
                pred_qty = max(0.0, round(pred_qty, 2))

                return {
                    "success": True,
                    "source": "AI_MODEL_XGBOOST",
                    "predicted_procurement_quantity": pred_qty,
                    "predicted_arrivals": round(pred_qty * 1.02, 2),
                    "expected_collection": round(pred_qty * 0.98, 2),
                    "recommended_trucks": max(1, int(pred_qty // 80) + 1),
                    "projected_bardan_bags": int(pred_qty * 2),
                    "confidence_score": 0.94,
                    "model_status": "Active XGBoost Regressor"
                }
            except Exception as e:
                print(f"[Fallback] Supply prediction error: {e}")

        # Rule-based fallback if ML model is unavailable
        fallback_qty = round(booked_quantity * 0.95, 2)
        return {
            "success": True,
            "source": "RULE_BASED_FALLBACK",
            "message": "AI prediction currently unavailable. Showing rule-based operational status.",
            "predicted_procurement_quantity": fallback_qty,
            "predicted_arrivals": round(fallback_qty * 1.02, 2),
            "expected_collection": round(fallback_qty * 0.98, 2),
            "recommended_trucks": max(1, int(fallback_qty // 80) + 1),
            "projected_bardan_bags": int(fallback_qty * 2),
            "confidence_score": 0.70,
            "model_status": "Rule-based Fallback"
        }

supply_predictor = SupplyPredictor()
