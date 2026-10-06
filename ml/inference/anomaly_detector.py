"""
Anomaly Detection Inference Engine using Isolation Forest.
Identifies potential anomalies across procurement chain transactions.
Labels output strictly as "Potential anomaly" (never "Fraud confirmed").
"""

import os
import joblib
import numpy as np

class AnomalyDetector:
    def __init__(self):
        self.bundle = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        model_path = os.path.join(base_dir, "ml", "models", "anomaly_detector_iforest.joblib")
        if os.path.exists(model_path):
            try:
                self.bundle = joblib.load(model_path)
                self.is_loaded = True
            except Exception as e:
                print(f"[Warning] Failed to load Isolation Forest anomaly model: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def evaluate_transaction(self, booked_qty: float, collected_qty: float,
                             weighed_qty: float, procured_qty: float,
                             moisture_content: float = 13.5, processing_time_mins: float = 60.0):
        qty_diff = round(abs(weighed_qty - booked_qty), 2)
        pct_diff = round((qty_diff / max(1.0, booked_qty)) * 100, 2)

        features = [
            booked_qty, collected_qty, weighed_qty, procured_qty,
            moisture_content, processing_time_mins, qty_diff
        ]

        if self.is_loaded:
            try:
                model = self.bundle["model"]
                X = np.array([features])
                score = float(model.decision_function(X)[0])
                pred = int(model.predict(X)[0]) # -1 = anomaly, 1 = normal

                is_anomaly = (pred == -1) or (pct_diff > 30.0) or (moisture_content > 17.0)

                # Determine Risk Level
                if pct_diff > 45.0 or score < -0.25:
                    risk = "CRITICAL"
                elif pct_diff > 25.0 or score < -0.10:
                    risk = "HIGH"
                elif is_anomaly:
                    risk = "MEDIUM"
                else:
                    risk = "LOW"

                reasons = []
                if pct_diff > 20.0:
                    reasons.append(f"Weighed quantity differs from booked quantity by {pct_diff}% ({qty_diff} Quintals).")
                if moisture_content > 16.0:
                    reasons.append(f"Moisture reading ({moisture_content}%) exceeds standard Fair Average Quality threshold.")
                if processing_time_mins > 180.0:
                    reasons.append(f"Unusually prolonged processing duration ({processing_time_mins} minutes) between arrival and weighment.")
                if not reasons and is_anomaly:
                    reasons.append("Multi-dimensional feature vector deviated from normal procurement baseline distribution.")

                reason_text = " | ".join(reasons) if reasons else "Parameters within standard statistical baseline."

                return {
                    "is_potential_anomaly": is_anomaly,
                    "is_anomaly": is_anomaly,
                    "label": "Potential Anomaly — Requires Review" if is_anomaly else "Normal Transaction",
                    "risk_level": risk,
                    "anomaly_score": round(score, 4),
                    "percentage_discrepancy": pct_diff,
                    "reasons": reason_text,
                    "reason": reason_text,
                    "status": "OPEN" if is_anomaly else "CLEARED",
                    "requires_human_review": is_anomaly,
                    "disclaimer": "Anomaly detection is an automated alerting mechanism and requires human verification.",
                    "model_source": "Isolation Forest"
                }
            except Exception as e:
                print(f"[Fallback] Anomaly detection error: {e}")

        # Rule-based fallback
        is_anom = pct_diff > 25.0 or moisture_content > 16.5
        risk = "HIGH" if pct_diff > 40.0 else ("MEDIUM" if is_anom else "LOW")
        return {
            "is_potential_anomaly": is_anom,
            "is_anomaly": is_anom,
            "label": "Potential Anomaly — Requires Review" if is_anom else "Normal Transaction",
            "risk_level": risk,
            "anomaly_score": -0.15 if is_anom else 0.15,
            "percentage_discrepancy": pct_diff,
            "reasons": f"Rule-based threshold triggered: discrepancy {pct_diff}%" if is_anom else "Within standard tolerance.",
            "reason": f"Rule-based threshold triggered: discrepancy {pct_diff}%" if is_anom else "Within standard tolerance.",
            "status": "OPEN" if is_anom else "CLEARED",
            "requires_human_review": is_anom,
            "disclaimer": "AI model unavailable. Evaluated using rule-based operational heuristic.",
            "model_source": "Rule-based Fallback"
        }

anomaly_detector = AnomalyDetector()
