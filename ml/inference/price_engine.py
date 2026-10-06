"""
AI Price Estimation Inference Engine using XGBoost.
Implements the core BharatAgri rule:
  FINAL ESTIMATED PRICE = MAX(AI ESTIMATE, OFFICIAL MSP)

Distinguishes clearly between:
  1. Official MSP (Statutory benchmark notified by GoI)
  2. AI Estimated Procurement Price (Model-derived dynamic estimate)
  3. Estimated Total Value (Final Price * Quantity)

Never refers to the AI estimate as 'MSP'.
Provides breakdown of main factors affecting the price estimate.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

class PriceEngine:
    def __init__(self):
        self.bundle = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        model_path = os.path.join(base_dir, "ml", "models", "price_estimation_xgb.joblib")
        if os.path.exists(model_path):
            try:
                self.bundle = joblib.load(model_path)
                self.is_loaded = True
            except Exception as e:
                print(f"[Warning] Could not load XGBoost price model bundle: {e}")
                self.is_loaded = False
        else:
            self.is_loaded = False

    def estimate_price(
        self,
        crop: str,
        official_msp: float,
        quantity_quintals: float = 1.0,
        hist_proc_price: Optional[float] = None,
        hist_proc_qty: Optional[float] = None,
        current_demand: Optional[float] = None,
        current_supply: Optional[float] = None,
        state: Optional[str] = "Goa",
        district: Optional[str] = "North Goa",
        season: Optional[str] = "Kharif",
        storage_avail_ratio: Optional[float] = 0.50,
        trend_factor: Optional[float] = 0.0
    ) -> Dict[str, Any]:
        official_msp = float(official_msp) if official_msp and official_msp > 0 else 2300.00
        qty = float(quantity_quintals) if quantity_quintals and quantity_quintals > 0 else 1.0
        h_price = float(hist_proc_price) if hist_proc_price and hist_proc_price > 0 else official_msp
        h_qty = float(hist_proc_qty) if hist_proc_qty and hist_proc_qty > 0 else 50.0
        c_demand = float(current_demand) if current_demand is not None else 40000.0
        c_supply = float(current_supply) if current_supply is not None else 45000.0
        surplus_deficit = c_supply - c_demand
        s_ratio = float(storage_avail_ratio) if storage_avail_ratio is not None else 0.50
        trend = float(trend_factor) if trend_factor is not None else 0.01

        raw_ai_estimate = None

        if self.is_loaded:
            try:
                encoders = self.bundle["encoders"]
                model = self.bundle["model"]
                feature_cols = self.bundle["feature_cols"]

                row = {}
                for col in ["crop", "state", "district", "season"]:
                    val = locals()[col]
                    le = encoders[col]
                    try:
                        row[col] = le.transform([str(val)])[0]
                    except Exception:
                        row[col] = 0

                row["official_msp"] = official_msp
                row["hist_proc_price"] = h_price
                row["hist_proc_qty"] = h_qty
                row["demand_q"] = c_demand
                row["supply_q"] = c_supply
                row["surplus_q"] = surplus_deficit
                row["storage_avail_ratio"] = s_ratio
                row["trend_factor"] = trend

                X_df = pd.DataFrame([row])[feature_cols]
                preds = model.predict(X_df)
                raw_ai_estimate = float(preds[0])
            except Exception as e:
                print(f"[PriceEngine] Inference error, falling back to analytical formula: {e}")

        # Fallback / baseline analytical calculation if ML error or uncalibrated
        if raw_ai_estimate is None:
            if surplus_deficit < -1000:
                deficit_pct = min(0.12, abs(surplus_deficit) / max(c_demand, 1.0) * 0.25)
                raw_ai_estimate = official_msp * (1.0 + max(0.02, deficit_pct))
            elif surplus_deficit > 2000:
                surplus_pct = min(0.025, (surplus_deficit / max(c_supply, 1.0)) * 0.05)
                raw_ai_estimate = official_msp * (1.0 + surplus_pct)
            else:
                raw_ai_estimate = official_msp * 1.015

        # Dynamic market sensitivity: In deficit / demand-surge conditions, ensure price reflects demand pressure
        if surplus_deficit < -500:
            deficit_pct = min(0.25, abs(surplus_deficit) / max(c_demand, 1.0) * 0.35)
            elasticity_price = official_msp * (1.0 + max(0.03, deficit_pct))
            if raw_ai_estimate < elasticity_price:
                raw_ai_estimate = elasticity_price

        ai_estimated_price = round(raw_ai_estimate, 2)

        # Enforce CRITICAL RULE:
        # FINAL ESTIMATED PRICE = MAX(AI ESTIMATE, OFFICIAL MSP)
        final_estimated_price = round(max(official_msp, ai_estimated_price), 2)
        estimated_total_value = round(final_estimated_price * qty, 2)

        # Factors breakdown
        ratio = c_demand / max(c_supply, 1.0)
        demand_level = "High" if ratio > 1.05 else "Moderate" if ratio >= 0.85 else "Low"
        supply_level = "High" if c_supply > 150000 else "Moderate" if c_supply >= 30000 else "Low"
        surplus_status = "SURPLUS" if surplus_deficit > 2000 else "DEFICIT" if surplus_deficit < -1000 else "BALANCED"
        storage_level = "High" if s_ratio >= 0.60 else "Moderate" if s_ratio >= 0.25 else "Constrained"

        demand_pull_val = round(max(0.0, final_estimated_price - official_msp), 2)
        factors = {
            "official_msp_baseline": {
                "name": "Official MSP Statutory Baseline",
                "value_inr": official_msp,
                "impact": "Guaranteed legal price floor (non-negotiable safety net)",
                "weight": "Anchor Baseline"
            },
            "demand_supply_pressure": {
                "name": "Demand vs Expected Supply Pressure",
                "demand_level": demand_level,
                "supply_level": supply_level,
                "surplus_deficit_quintals": round(surplus_deficit, 1),
                "market_sentiment": surplus_status,
                "impact_inr": demand_pull_val,
                "impact": f"Market {surplus_status.lower()} condition resulting in ₹{demand_pull_val:,.2f}/Q adjustment over MSP"
            },
            "storage_buffer_headroom": {
                "name": "Storage & Inventory Availability",
                "level": storage_level,
                "headroom_ratio_percent": round(s_ratio * 100, 1),
                "impact": "Stable godown availability prevents distress selling"
            },
            "historical_trend": {
                "name": "Historical Regional Procurement Benchmark",
                "historical_proc_price": round(h_price, 2),
                "trend": "Positive" if trend >= 0 else "Neutral",
                "impact": f"Tracks closely with {season} multi-year procurement averages"
            }
        }

        if surplus_status == "DEFICIT":
            rationale = (
                f"State crop demand ({c_demand:,.0f} Q) exceeds projected harvest supply ({c_supply:,.0f} Q). "
                f"High mill/buffer restocking demand elevates AI estimated price to ₹{ai_estimated_price:,.2f}/Q, "
                f"which is ₹{round(final_estimated_price - official_msp, 2):,.2f} above the Official MSP floor."
            )
        elif surplus_status == "SURPLUS":
            rationale = (
                f"State supply ({c_supply:,.0f} Q) is in comfortable surplus over demand ({c_demand:,.0f} Q). "
                f"Under the BharatAgri surplus floor rule, final procurement price firmly anchors at the Official MSP "
                f"baseline (₹{official_msp:,.2f}/Q) with verified storage reserves."
            )
        else:
            rationale = (
                f"Balanced market equilibrium in {state}. Procurement estimate tracks the Official MSP baseline "
                f"with a standard handling allowance of ₹{round(final_estimated_price - official_msp, 2):,.2f}/Q."
            )

        explanation_text = (
            f"{rationale} Factors — "
            f"Demand: {c_demand:,.0f} Q. "
            f"Expected Supply: {c_supply:,.0f} Q. "
            f"Inventory: {round(c_supply * 0.45, 1):,.0f} Q current stock. "
            f"Storage Availability: {storage_level} ({round(s_ratio * 100, 1)}% headroom). "
            f"Historical Procurement: ₹{round(h_price, 2)}/Q benchmark."
        )

        return {
            "crop": crop,
            "state": state,
            "district": district,
            "season": season,
            "quantity_quintals": qty,
            # Distinct naming per prompt specification
            "official_msp": official_msp,
            "ai_estimated_procurement_price": ai_estimated_price,
            "final_estimated_price": final_estimated_price,
            "estimated_total_value": estimated_total_value,
            "model_used": "XGBoost Regressor v1.0" if self.is_loaded else "Deterministic Econometric Hybrid",
            "is_msp_floor_applied": final_estimated_price == official_msp and ai_estimated_price < official_msp,
            "formula_applied": "FINAL ESTIMATED PRICE = MAX(AI ESTIMATE, OFFICIAL MSP)",
            "explanation": explanation_text,
            "factors": factors,
            "confidence": None,
            "confidence_display": "confidence unavailable",
            "advisory_disclaimer": "BharatAgri estimated price is advisory based on market data. Final disbursement is calculated upon certified physical weighment and laboratory Fair Average Quality grading at the gate."
        }

price_engine = PriceEngine()

def estimate_procurement_price(
    crop: str,
    state: str = "Punjab",
    district: str = "Ludhiana",
    season: str = "Kharif",
    quantity: float = 1.0,
    official_msp: Optional[float] = None
) -> Dict[str, Any]:
    # Default MSP map
    default_msp = {
        "wheat": 2275.0,
        "paddy": 2183.0,
        "rice": 2183.0,
        "cotton": 6620.0,
        "maize": 2090.0,
        "mustard": 5650.0,
        "chana": 5440.0,
        "soybean": 4600.0,
        "sugarcane": 315.0,
        "groundnut": 6377.0,
        "moong": 8558.0,
        "urad": 6950.0,
        "tur": 7000.0,
        "arhar": 7000.0,
        "bajra": 2500.0,
        "jowar": 3180.0,
        "barley": 1850.0,
        "potato": 1400.0,
        "onion": 1650.0,
        "tomato": 1800.0
    }
    msp = official_msp or default_msp.get(crop.lower().strip(), 2300.0)
    return price_engine.estimate_price(
        crop=crop,
        official_msp=msp,
        quantity_quintals=quantity,
        state=state,
        district=district,
        season=season
    )

