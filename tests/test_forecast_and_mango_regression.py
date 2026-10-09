"""
Comprehensive Regression Tests for:
1. Government Supply Forecast: Historical physical data restoration, dynamic anchor date,
   monthly aggregation support, model-generated Projected Procurement, transition continuity,
   and honest insufficient-data handling.
2. Mango AI: Accurate fruit boundary refinement, exclusion of external cast shadows,
   protection of healthy dark green and dark yellow mango peel, smooth illumination shadow preservation,
   and adaptive internal padding without treating segmentation failures as 100% defect.
"""

import os
import sys
import pytest
from datetime import date
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.procurement import ProcurementRecord
from ml.inference.mango_detector import MangoDetector
from ml.inference.mango_quality_scanner import MangoQualityScanner
from ml.inference.supply_predictor import supply_predictor

client = TestClient(app)


@pytest.fixture(scope="module")
def gov_auth_headers():
    res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "GOVERNMENT"
    })
    assert res.status_code == 200, f"Gov login failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# PART 1: GOVERNMENT SUPPLY FORECAST REGRESSION TESTS
# =========================================================================

def test_government_forecast_historical_data_restored(gov_auth_headers):
    """
    Verifies that all verified historical records in the database (including up to Oct 15)
    are retained and visible in the daily month forecast without artificial cutoff.
    """
    res = client.get("/api/government/analytics/forecast-vs-actual?range=month&interval=daily", headers=gov_auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Must contain historical points
    hist_points = [p for p in data if not p["is_future"]]
    assert len(hist_points) >= 15, f"Expected at least 15 historical points, got {len(hist_points)}"

    # Check anchor date records exist (e.g. 15 Oct)
    dates = [p["period_date"] for p in hist_points]
    assert "2026-10-15" in dates, "2026-10-15 must be present in historical observations"

    # Actual quantity must be positive
    oct15 = next(p for p in hist_points if p["period_date"] == "2026-10-15")
    assert oct15["actual_quantity"] > 1000.0, f"Oct 15 actual intake should be > 1000 Q, got {oct15['actual_quantity']}"


def test_government_forecast_projected_procurement_non_zero_and_connected(gov_auth_headers):
    """
    Verifies that Projected Procurement is generated via XGBoost, is non-zero,
    and has a seamless transition point connecting historical with future projections.
    """
    res = client.get("/api/government/analytics/forecast-vs-actual?range=month&interval=daily", headers=gov_auth_headers)
    assert res.status_code == 200
    body = res.json()
    data = body["data"]

    # Transition point verification
    transition_points = [p for p in data if p.get("is_transition") is True]
    assert len(transition_points) == 1, "There must be exactly one transition point anchoring history to projection"
    t_pt = transition_points[0]
    assert t_pt["actual_quantity"] == t_pt["predicted_quantity"], "Transition point must connect actual with predicted line"

    # Future projection verification
    future_points = [p for p in data if p["is_future"]]
    assert len(future_points) > 0, "Future projected points must exist"
    for fp in future_points:
        assert fp["predicted_quantity"] is not None
        assert fp["predicted_quantity"] > 0, f"Projected procurement must be positive, got {fp['predicted_quantity']}"
        assert fp["actual_quantity"] is None, "Future points must not present actual observations"
        assert fp["uncertainty_lower"] is not None
        assert fp["uncertainty_upper"] is not None
        assert fp["uncertainty_lower"] <= fp["predicted_quantity"] <= fp["uncertainty_upper"]


def test_government_forecast_monthly_aggregation_honored(gov_auth_headers):
    """
    Verifies that setting interval='monthly' produces monthly seasonal buckets (Sep, Oct, Nov, Dec...)
    even when date_range='month' or 'week'.
    """
    res = client.get("/api/government/analytics/forecast-vs-actual?range=month&interval=monthly", headers=gov_auth_headers)
    assert res.status_code == 200
    body = res.json()
    data = body["data"]

    # In monthly view, periods must be monthly strings
    assert len(data) >= 4, f"Monthly view should return monthly buckets, got {len(data)}"
    assert any("Sep 2026" in p["period"] for p in data)
    assert any("Oct 2026" in p["period"] for p in data)
    assert any("Nov 2026" in p["period"] for p in data)

    # Oct 2026 to date should be anchored to projections
    oct_pt = next(p for p in data if "Oct 2026" in p["period"])
    assert oct_pt["actual_quantity"] > 200000.0, "Monthly Oct 2026 verified intake should be > 200,000 Q"
    assert oct_pt["is_transition"] is True


def test_government_forecast_insufficient_data_status(gov_auth_headers):
    """
    Verifies that selecting a crop with zero historical observations (e.g. Mustard or Onion)
    transparently returns data_status='INSUFFICIENT_DATA' rather than faking historical observations.
    """
    res = client.get("/api/government/analytics/forecast-vs-actual?crop=Mustard&range=month&interval=daily", headers=gov_auth_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["data_status"] == "INSUFFICIENT_DATA"
    assert body["summary"]["has_sufficient_history"] is False


# =========================================================================
# PART 2: MANGO AI SEGMENTATION, SHADOWS & PADDING REGRESSION TESTS
# =========================================================================

def test_mango_external_cast_shadow_excluded_from_mask():
    """
    Simulates a clean white table with a mango and an external cast shadow.
    Verifies that the external grey shadow on the white table is excluded from the fruit mask.
    """
    detector = MangoDetector()
    img_arr = np.full((300, 300, 3), 250, dtype=np.uint8)  # White background

    # Draw round yellow/green mango at center
    yy, xx = np.ogrid[:300, :300]
    fruit_dist = np.hypot(xx - 140, yy - 140)
    fruit_zone = fruit_dist < 60
    img_arr[fruit_zone] = [220, 180, 35]  # Ripe golden mango

    # Draw external cast shadow extending to the right over white sheet
    shadow_zone = (fruit_dist >= 60) & (fruit_dist < 85) & (xx > 140) & (yy > 120)
    img_arr[shadow_zone] = [170, 170, 170]  # Neutral grey cast shadow on white table

    test_img = Image.fromarray(img_arr)
    _, mangoes, debug = detector.detect_mangoes(test_img, return_debug=True)

    assert len(mangoes) == 1, f"Expected 1 mango detected, got {len(mangoes)}"
    m = mangoes[0]
    inst_mask = m["mask"]

    # Verify shadow region is NOT included in the final fruit mask
    shadow_overlap = np.sum(inst_mask & shadow_zone)
    shadow_total = np.sum(shadow_zone)
    leakage_ratio = shadow_overlap / max(1, shadow_total)
    assert leakage_ratio < 0.05, f"External shadow leaked into fruit mask: {leakage_ratio*100:.1f}%"


def test_mango_healthy_dark_peel_not_marked_as_defect():
    """
    Simulates a healthy mango with dark green peel (L=35, high chlorophyll)
    and darker yellow/ochre skin. Verifies 0% defect rate.
    """
    scanner = MangoQualityScanner()

    # Create dark green mango crop on white background
    crop_arr = np.full((120, 120, 3), 255, dtype=np.uint8)
    yy, xx = np.ogrid[:120, :120]
    fruit_mask = np.hypot(xx - 60, yy - 60) < 45

    # Dark green peel: R=30, G=70, B=25 (L ~ 52, G >> R, G >> B)
    crop_arr[fruit_mask] = [32, 68, 22]
    crop_img = Image.fromarray(crop_arr)

    d_res = scanner.analyze_fruit_defects(crop_img, inst_mask=fruit_mask)
    assert d_res["affected_area_pct"] == 0.0, f"Dark green peel was falsely classified as defect: {d_res['affected_area_pct']}%"
    assert d_res["visible_defects"] == ["None (Sound Surface)"]


def test_mango_gradual_shadow_gradient_not_marked_as_defect():
    """
    Simulates a healthy golden mango with a gradual lighting shadow across its surface.
    Verifies that the surface shadow gradient is preserved as fruit and not counted as a defect.
    """
    scanner = MangoQualityScanner()

    crop_arr = np.full((120, 120, 3), 255, dtype=np.uint8)
    yy, xx = np.ogrid[:120, :120]
    fruit_mask = np.hypot(xx - 60, yy - 60) < 45

    # Base yellow skin with gradual illumination gradient across horizontal axis
    for y in range(120):
        for x in range(120):
            if fruit_mask[y, x]:
                # Gradual shadow factor: 1.0 on left, 0.55 on right (smooth shading)
                factor = 1.0 - 0.45 * (x / 120.0)
                crop_arr[y, x] = [int(220 * factor), int(180 * factor), int(30 * factor)]

    crop_img = Image.fromarray(crop_arr)
    d_res = scanner.analyze_fruit_defects(crop_img, inst_mask=fruit_mask)
    assert d_res["affected_area_pct"] < 0.5, f"Lighting gradient caused false defect: {d_res['affected_area_pct']}%"


def test_mango_adaptive_inner_padding_and_defect_denominator():
    """
    Verifies that internal padding margin is slight (2-8px),
    and defect percentage is strictly calculated using valid inner analysis mask as denominator:
    Defect% = accepted_defect_pixels / inner_mango_pixels * 100.
    """
    scanner = MangoQualityScanner()

    crop_arr = np.full((140, 140, 3), 255, dtype=np.uint8)
    yy, xx = np.ogrid[:140, :140]
    fruit_mask = np.hypot(xx - 70, yy - 70) < 55
    crop_arr[fruit_mask] = [230, 190, 40]  # Golden skin

    # Place a genuine necrotic black lesion near the center (radius 8px)
    lesion_mask = np.hypot(xx - 65, yy - 65) < 8
    crop_arr[lesion_mask] = [15, 12, 10]  # Necrotic black spot

    crop_img = Image.fromarray(crop_arr)
    d_res = scanner.analyze_fruit_defects(crop_img, inst_mask=fruit_mask)

    assert 2 <= d_res["padding_margin_px"] <= 8, f"Padding margin out of expected bounds: {d_res['padding_margin_px']}"
    assert d_res["inner_mango_pixels"] > 0
    assert d_res["accepted_defect_pixels"] > 0
    expected_pct = round(float(d_res["accepted_defect_pixels"]) / float(d_res["inner_mango_pixels"]) * 100.0, 2)
    assert d_res["affected_area_pct"] == expected_pct, "Defect % must exactly match accepted / inner * 100 formula"


def test_mango_segmentation_failure_never_returns_100_percent_defect():
    """
    Verifies that an invalid crop or segmentation failure returns
    segmentation_status='NEEDS_REVIEW' and 0.0% defect, never a false 100% defect rate.
    """
    scanner = MangoQualityScanner()

    # Empty image with no fruit pixels
    empty_crop = Image.new("RGB", (100, 100), (255, 255, 255))
    d_res = scanner.analyze_fruit_defects(empty_crop, inst_mask=np.zeros((100, 100), dtype=bool))

    assert d_res["affected_area_pct"] == 0.0
    assert d_res["segmentation_status"] == "NEEDS_REVIEW"
    assert d_res["segmentation_failure"] is True
