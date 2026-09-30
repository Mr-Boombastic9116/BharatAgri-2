"""
Congestion Prediction Engine.
Calculates operational congestion level based on:
  total_load = predicted_arrivals + existing_bookings + expected_collection
  utilization_percent = (total_load / daily_capacity) * 100

Operational Thresholds:
  0–50%     LOW
  50–75%    MEDIUM
  75–90%    HIGH
  90%+      CRITICAL
Note: These are BharatAgri system operational thresholds.
"""

def calculate_congestion(predicted_arrivals: float, existing_bookings_qty: float,
                         expected_collection_qty: float, daily_capacity: float):
    if daily_capacity <= 0:
        daily_capacity = 800.0

    # Total load considers active bookings and arriving produce
    # Weight arriving produce and bookings
    total_load = round(existing_bookings_qty + (predicted_arrivals * 0.35) + (expected_collection_qty * 0.25), 2)
    utilization_pct = round((total_load / daily_capacity) * 100, 2)

    if utilization_pct >= 90.0:
        level = "CRITICAL"
        action = "Initiate dynamic centre redirection and dispatch additional logistics."
    elif utilization_pct >= 75.0:
        level = "HIGH"
        action = "Restrict new walk-in allocations; alert operational staff."
    elif utilization_pct >= 50.0:
        level = "MEDIUM"
        action = "Normal operational queue; monitor slot arrival velocity."
    else:
        level = "LOW"
        action = "Ample operational capacity available for expedited processing."

    return {
        "predicted_arrivals": round(predicted_arrivals, 2),
        "existing_bookings_qty": round(existing_bookings_qty, 2),
        "expected_collection_qty": round(expected_collection_qty, 2),
        "daily_capacity": round(daily_capacity, 2),
        "total_estimated_load": total_load,
        "utilization_percent": utilization_pct,
        "congestion_level": level,
        "recommended_action": action,
        "threshold_guide": "0-50% LOW, 50-75% MEDIUM, 75-90% HIGH, 90%+ CRITICAL",
        "thresholds_reference": {
            "0-50%": "LOW",
            "50-75%": "MEDIUM",
            "75-90%": "HIGH",
            "90%+": "CRITICAL"
        }
    }
