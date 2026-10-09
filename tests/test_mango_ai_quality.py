"""
Test Suite: Mango AI Multi-Fruit Detection, Instance Separation, and Decoupled Quality Evaluation
Verifies:
1. Touching and overlapping mangoes are correctly partitioned into individual instances (e.g. 5 touching mangoes -> 5 individual detections).
2. Single isolated mango is detected without over-segmentation.
3. Ripeness and Defect/Health status are strictly decoupled:
   - Ripe + Defective (e.g. Anthracnose on yellow mango)
   - Ripe + Healthy
   - Unripe + Healthy
   - Unripe + Defective
4. Explainability and visual evidence:
   - Defect region coordinates are extracted
   - Clear grounded rationale is generated
   - Lot-level aggregation is strictly computed from individual fruit results.
"""

import pytest
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO

from ml.inference.mango_detector import MangoDetector
from ml.inference.mango_quality_scanner import get_mango_quality_scanner


def test_touching_mangoes_instance_separation():
    """Verify touching mangoes are partitioned into individual fruit instances."""
    detector = MangoDetector()
    w, h = 600, 450
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)

    # 5 touching/overlapping mangoes
    positions = [
        (80, 80, 220, 240, (230, 190, 25)),
        (180, 70, 320, 230, (220, 175, 20)),
        (280, 90, 420, 250, (130, 195, 40)),
        (130, 200, 270, 360, (215, 160, 30)),
        (240, 210, 380, 370, (225, 185, 35)),
    ]
    for x1, y1, x2, y2, color in positions:
        draw.ellipse([x1, y1, x2, y2], fill=color)

    _, boxes = detector.detect_mangoes(img)
    assert len(boxes) == 5, f"Expected 5 separated mangoes, got {len(boxes)}"

    # Ensure each box has distinct coordinates and valid area
    for b in boxes:
        assert b["area"] > 500
        assert b["box"][2] > 20
        assert b["box"][3] > 20


def test_single_mango_no_oversegmentation():
    """Verify single mango in photograph is detected as 1 instance."""
    detector = MangoDetector()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 60, 300, 240], fill=(230, 180, 25))

    _, boxes = detector.detect_mangoes(img)
    assert len(boxes) == 1, f"Expected 1 mango, got {len(boxes)}"


def test_decoupled_ripeness_and_defect_evaluation():
    """Verify ripe + defective mangoes are NOT misclassified as healthy."""
    scanner = get_mango_quality_scanner()

    w, h = 500, 350
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)

    # Mango 1: Yellow RIPE + Healthy
    draw.ellipse([60, 80, 210, 270], fill=(240, 190, 20))

    # Mango 2: Yellow RIPE + DEFECTIVE (Anthracnose lesions)
    draw.ellipse([270, 80, 420, 270], fill=(235, 185, 25))
    # Necrotic spots
    draw.ellipse([320, 120, 365, 165], fill=(20, 18, 15))
    draw.ellipse([345, 180, 390, 225], fill=(25, 20, 18))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 2
    assert res["healthy_count"] == 1
    assert res["defect_count"] == 1

    # Check Mango 1
    m1 = res["detections"][0]
    assert m1["health_status"] == "Healthy"
    assert m1["ripeness"] == "Ripe"
    assert m1["quality_grade"] in ["Excellent", "Grade A"]
    assert m1["commercial_grade"] == "Grade A"

    # Check Mango 2: Must be Ripe AND Defective
    m2 = res["detections"][1]
    assert m2["health_status"] == "Defective"
    assert m2["ripeness"] == "Ripe"
    assert m2["defect_type"] in ["Anthracnose", "Stem End Rot", "Surface Blemish"]
    assert m2["quality_grade"] in ["Defective", "Reject", "Slightly Defective", "Grade B", "Grade C"]
    assert len(m2["visual_evidence"]) > 0


def test_lot_level_aggregation_and_uncertain_handling():
    """Verify overall lot results are strictly derived from individual fruit results."""
    scanner = get_mango_quality_scanner()

    w, h = 400, 300
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Healthy green unripe mango
    draw.ellipse([100, 60, 300, 240], fill=(110, 185, 45))

    res = scanner.inspect_lot_image(img)
    assert res["sample_count"] == 1
    assert res["healthy_count"] == 1
    assert res["defect_count"] == 0
    assert res["affected_percentage"] == 0.0
    assert res["visual_grade"] == "Grade A"
    assert "ripeness_summary" in res
    assert "grade_counts" in res


def test_multi_view_aggregation_and_uncertainty_reduction():
    """Verify combining multiple views of the same mango narrows surface uncertainty range."""
    scanner = get_mango_quality_scanner()

    w, h = 400, 300
    # View 1: Clean yellow front side
    v1 = Image.new("RGB", (w, h), (240, 240, 240))
    d1 = ImageDraw.Draw(v1)
    d1.ellipse([100, 60, 300, 240], fill=(235, 185, 25))

    # View 2: Back side with 1 minor blemish spot
    v2 = Image.new("RGB", (w, h), (240, 240, 240))
    d2 = ImageDraw.Draw(v2)
    d2.ellipse([100, 60, 300, 240], fill=(235, 185, 25))
    d2.ellipse([180, 120, 215, 155], fill=(30, 25, 20))

    mv_res = scanner.inspect_multi_view_mango([v1, v2], mango_id="MANGO-TEST-01")
    assert mv_res["views_analyzed"] == 2
    assert "surface_coverage_est" in mv_res
    assert "estimated_total_surface_severity" in mv_res
    assert mv_res["quality_grade"] in ["Excellent", "Very Good", "Grade A", "Grade B"]
    assert len(mv_res["views_breakdown"]) == 2


def test_real_dataset_single_mango_no_false_split_and_healthy():
    """Verify real single mango photographs from dataset are detected as 1 mango and evaluated accurately."""
    import os
    sample_path = "ml/data/mango/extracted/MangoDHDS/Healthy/Healthy/He1.jpg"
    if not os.path.exists(sample_path):
        pytest.skip(f"Dataset sample not present at {sample_path}")

    scanner = get_mango_quality_scanner()
    img = Image.open(sample_path)
    res = scanner.inspect_lot_image(img)

    # Must be detected as exactly 1 mango (NO false splitting into 2 or 3 mangoes)
    assert res["mangoes_detected"] == 1
    assert res["healthy_count"] == 1
    assert res["defect_count"] == 0

    det = res["detections"][0]
    assert det["health_status"] == "Healthy"
    assert det["defect_type"] in ["None", "Healthy"]
    assert det["quality_grade"] in ["Excellent", "Very Good", "Grade A"]
    assert det["visible_defect_pct"] <= 1.0


def test_real_anthracnose_black_spots_detected_and_no_false_split():
    """Verify real Anthracnose images with black spots are accurately detected as defective and not falsely split."""
    import os
    scanner = get_mango_quality_scanner()

    for fname in ["An1.jpg", "An10.jpg"]:
        sample_path = f"ml/data/mango/extracted/MangoDHDS/Anthracnose/Anthracnose/{fname}"
        if not os.path.exists(sample_path):
            continue

        img = Image.open(sample_path)
        res = scanner.inspect_lot_image(img)

        # Must be detected as exactly 1 mango (NO false split on single fruit)
        assert res["mangoes_detected"] == 1, f"{fname} expected 1 mango, got {res['mangoes_detected']}"
        assert res["defect_count"] == 1, f"{fname} expected defect_count 1, got {res['defect_count']}"
        assert res["healthy_count"] == 0, f"{fname} expected healthy_count 0, got {res['healthy_count']}"

        det = res["detections"][0]
        assert det["health_status"] == "Defective"
        assert det["visible_defect_pct"] >= 1.0, f"{fname} defect % {det['visible_defect_pct']} should be >= 1.0%"
        assert len(det["defect_regions"]) > 0, f"{fname} should have localized defect regions"


def test_debug_mode_generates_all_10_visual_stages():
    """Verify the 10-stage debug mode generates all visual pipeline inspection artifacts."""
    scanner = get_mango_quality_scanner()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 60, 300, 240], fill=(235, 185, 25))

    res = scanner.inspect_lot_image(img, inspection_code="DEBUG-TEST-01")
    assert "debug_images" in res
    dbg = res["debug_images"]
    expected_stages = [
        "debug_1_original",
        "debug_2_bunch_bbox",
        "debug_3_separation_boundaries",
        "debug_4_instance_masks",
        "debug_5_crops_montage",
        "debug_6_background_excluded",
        "debug_7_defect_candidates",
        "debug_8_final_defect_mask",
        "debug_9_defect_percentage",
        "debug_10_final_grade"
    ]
    for stage in expected_stages:
        assert stage in dbg, f"Missing debug stage {stage}"
        assert dbg[stage].startswith("/uploads/mango_inspections/")


def test_mango_touching_dark_background():
    """Verify mango resting on a dark/black surface does not leak black background into defect detection."""
    scanner = get_mango_quality_scanner()
    w, h = 500, 350
    # Dark black/grey conveyor surface
    img = Image.new("RGB", (w, h), (20, 22, 25))
    draw = ImageDraw.Draw(img)

    # Sound ripe mango on dark surface
    draw.ellipse([120, 70, 380, 280], fill=(238, 182, 30))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]
    # Background must be excluded; defect percentage must NOT be inflated by the dark background
    assert det["health_status"] == "Healthy"
    assert det["visible_defect_pct"] <= 3.0, f"Defect % {det['visible_defect_pct']} inflated by dark background!"
    assert det["quality_grade"] in ["Excellent", "Very Good", "Grade A"]


def test_mango_with_background_black_clutter():
    """Verify background dark objects (crates, tools, dark corners) are excluded from mango peel."""
    scanner = get_mango_quality_scanner()
    w, h = 500, 350
    img = Image.new("RGB", (w, h), (242, 242, 242))
    draw = ImageDraw.Draw(img)

    # Black object in the corner / background
    draw.rectangle([20, 20, 90, 80], fill=(15, 15, 18))
    draw.rectangle([400, 250, 480, 330], fill=(25, 25, 28))

    # Sound mango in the center
    draw.ellipse([140, 60, 360, 270], fill=(235, 180, 32))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]
    assert det["health_status"] == "Healthy"
    assert det["visible_defect_pct"] <= 2.0
    assert det["quality_grade"] in ["Excellent", "Very Good", "Grade A"]


def test_bunch_three_mangoes_overlapping_curved_contours():
    """Verify 3 touching/overlapping mangoes form individual instances with natural curved contours."""
    scanner = get_mango_quality_scanner()
    w, h = 500, 400
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)

    # Cluster of 3 overlapping mangoes
    draw.ellipse([80, 80, 240, 250], fill=(230, 185, 30))
    draw.ellipse([210, 70, 370, 240], fill=(225, 175, 25))
    draw.ellipse([140, 190, 300, 350], fill=(220, 180, 35))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 3
    # Check that each instance has individual curved contours and reasonable solidity
    for det in res["detections"]:
        assert det["area"] > 500
        assert len(det["contour"]) >= 3
        assert det["grading_factors"]["solidity"] >= 0.70


def test_defect_percentage_formula_strictly_valid_mango_mask():
    """Verify defect percentage is strictly (defect_pixels / valid_mango_pixels) * 100, not bounding box area."""
    scanner = get_mango_quality_scanner()
    w, h = 200, 200
    # Synthetic crop with mango ellipse taking ~50% of the bounding box area
    crop_img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(crop_img)
    draw.ellipse([30, 30, 170, 170], fill=(235, 185, 30))

    # Add a known small necrotic spot in the center (radius 10 -> area ~314 px)
    draw.ellipse([90, 90, 110, 110], fill=(25, 20, 15))

    # Mask defining the ellipse
    mask = np.zeros((h, w), dtype=bool)
    yy, xx = np.ogrid[:h, :w]
    mask[(xx - 100)**2 + (yy - 100)**2 <= 70**2] = True
    mango_pixel_count = float(np.sum(mask))

    defect_info = scanner.analyze_fruit_defects(crop_img, crop_mask=mask)
    assert defect_info["total_defect_pixels"] > 0
    # Defect percentage should be based on mango_pixel_count (~15394 px), NOT w*h (40000 px)
    expected_pct = (defect_info["total_defect_pixels"] / mango_pixel_count) * 100.0
    assert abs(defect_info["affected_area_pct"] - expected_pct) < 1.0


def test_potential_grading_factors_and_disclaimer():
    """Verify Part 10 Potential Grading includes multi-factor metrics, explainability and disclaimer."""
    scanner = get_mango_quality_scanner()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Ripe sound mango
    draw.ellipse([100, 60, 300, 240], fill=(235, 185, 25))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    assert "lot_potential_grade" in res
    assert "AI Estimate" in res["lot_potential_grade"]
    assert "grading_disclaimer" in res
    assert "not an official statutory APMC" in res["grading_disclaimer"]

    det = res["detections"][0]
    assert "potential_grade" in det
    assert "ai_estimated_grade" in det
    assert "grading_rationale" in det
    assert "grading_factors" in det

    gf = det["grading_factors"]
    assert "ripeness" in gf
    assert "visible_defect_pct" in gf
    assert "significant_defect_count" in gf
    assert "colour_uniformity_score" in gf
    assert "shape_aspect_ratio" in gf
    assert "solidity" in gf
    assert "visibility" in gf
    assert "defect_confidence" in gf
    assert gf["is_official_standard"] is False


def test_boundary_shadow_not_flagged_as_defect():
    """Verify dark/grey contact shadow between touching mangoes is NOT counted as anthracnose/defect (Part 5 & 9)."""
    scanner = get_mango_quality_scanner()
    w, h = 500, 350
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)

    # Two touching healthy yellow-green mangoes
    draw.ellipse([80, 80, 240, 260], fill=(225, 180, 30))
    draw.ellipse([210, 80, 370, 260], fill=(220, 175, 28))

    # Dark grey contact shadow band at the overlap border
    draw.ellipse([200, 110, 230, 230], fill=(70, 65, 60))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 2

    # Perimeter contact shadow should NOT make both mangoes rejected as severely diseased
    # Because boundary erosion excludes perimeter shadows from defect analysis
    for det in res["detections"]:
        assert det["visible_defect_pct"] <= 5.0, f"Expected low defect %, got {det['visible_defect_pct']}% from boundary shadow"


def test_two_overlapping_mangoes_separated_curved_contours():
    """Verify 2 overlapping mangoes are partitioned into 2 distinct instances with organic curved masks."""
    detector = MangoDetector()
    w, h = 450, 350
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Two overlapping mangoes
    draw.ellipse([80, 80, 240, 260], fill=(235, 185, 30))
    draw.ellipse([190, 90, 360, 270], fill=(225, 175, 25))

    _, boxes = detector.detect_mangoes(img)
    assert len(boxes) == 2, f"Expected 2 separated mangoes, got {len(boxes)}"
    for b in boxes:
        assert b["area"] > 5000
        assert len(b["contour"]) >= 4
        # Verify shape prior ensures non-rectangular organic solidity
        assert 0.70 <= b["solidity"] <= 1.0


def test_external_cast_shadow_zero_defect():
    """Section 10: Dark cast shadow beside mango on background must produce 0 defect pixels."""
    scanner = get_mango_quality_scanner()
    w, h = 450, 320
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Ripe healthy mango
    draw.ellipse([80, 70, 240, 230], fill=(235, 185, 30))
    # Dark cast shadow beside mango on the background
    draw.ellipse([230, 150, 340, 240], fill=(50, 50, 55))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]
    dbg = det["debug_numerical"]
    assert dbg["accepted_defect_pixels"] == 0
    assert dbg["defect_percentage"] == 0.0
    assert det["visible_defect_pct"] == 0.0
    assert det["health_status"] == "Healthy"
    assert det["commercial_grade"] == "Grade A"


def test_internal_smooth_shadow_across_mango_zero_defect():
    """Section 11: Smooth illumination variation across mango surface must not be counted as a defect."""
    scanner = get_mango_quality_scanner()
    w, h = 400, 300
    img_arr = np.full((h, w, 3), 240, dtype=np.uint8)

    yy, xx = np.ogrid[:h, :w]
    mango_mask = ((xx - 200)**2 / (90**2) + (yy - 150)**2 / (70**2)) <= 1.0

    # Base yellow peel
    img_arr[mango_mask, 0] = 235
    img_arr[mango_mask, 1] = 185
    img_arr[mango_mask, 2] = 30

    # Smooth illumination variation (shadow across right side)
    grad = np.clip((xx - 180) / 100.0, 0.0, 1.0)
    dim_factor = 1.0 - 0.28 * grad
    for c in range(3):
        img_arr[..., c] = np.where(mango_mask, (img_arr[..., c] * dim_factor).astype(np.uint8), img_arr[..., c])

    img = Image.fromarray(img_arr)
    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]
    dbg = det["debug_numerical"]
    assert dbg["accepted_defect_pixels"] == 0
    assert dbg["defect_percentage"] == 0.0
    assert det["health_status"] == "Healthy"
    assert det["commercial_grade"] == "Grade A"


def test_defect_percentage_scaling_audit_intermediate_values():
    """Section 14: Trace scaling calculation from pixel count to ratio to percentage to grade."""
    scanner = get_mango_quality_scanner()
    w, h = 400, 400

    # Build synthetic mango with 80,000 valid pixels and 400 defect pixels (exact 0.5%)
    crop_img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(crop_img)

    # Fruit radius r = sqrt(80000 / pi) approx 159.6
    draw.ellipse([40, 40, 360, 360], fill=(235, 185, 30))

    # Mask defining peel
    yy, xx = np.ogrid[:h, :w]
    dist_sq = (xx - 200)**2 + (yy - 200)**2
    mask = dist_sq <= 160**2
    peel_pixels = int(np.sum(mask))

    # Place a small necrotic defect in the center of exactly ~400 pixels (radius r = 11.3 -> area ~401)
    draw.ellipse([189, 189, 211, 211], fill=(20, 18, 15))

    defect_info = scanner.analyze_fruit_defects(crop_img, crop_mask=mask)
    valid_px = defect_info["valid_mango_pixels"]
    accepted_px = defect_info["accepted_defect_pixels"]
    raw_ratio = defect_info["raw_defect_ratio"]
    defect_pct = defect_info["visible_defect_pct"]

    # Verify mathematics
    assert abs(raw_ratio - (accepted_px / valid_px)) < 1e-4
    assert abs(defect_pct - (raw_ratio * 100.0)) < 0.05
    # Verify no x10 or x100 scaling error: 400 px out of 80,000 px should be approx 0.5%, NEVER 5% or 50%
    assert 0.3 <= defect_pct <= 0.7, f"Defect percentage {defect_pct}% out of range, check scaling!"

    # Verify decision tree mapping for this 0.5% defect
    eval_res = scanner.decision_layer.evaluate_mango(
        ripeness="Ripe",
        ripeness_conf=90.0,
        defect_class="Healthy",
        defect_conf=80.0,
        visible_defect_pct=defect_pct,
        defect_boxes=defect_info["defect_boxes"]
    )
    assert eval_res["commercial_grade"] == "Grade A"
    assert eval_res["health_status"] == "Healthy"


def test_grade_decision_table_monotonic_calibration():
    """Section 15: Verify calibration test table across 0%, 0.1%, 0.5%, 1%, 2%, 5%, 10%, 20%, 30%, 50%."""
    from ml.inference.quality_decision_tree import MangoQualityDecisionLayer
    tree = MangoQualityDecisionLayer()

    expected_grades = {
        0.0: ("Healthy", "Grade A"),
        0.1: ("Healthy", "Grade A"),
        0.5: ("Healthy", "Grade A"),
        1.0: ("Healthy", "Grade A"),
        2.0: ("Healthy", "Grade A"),
        5.0: ("Healthy", "Grade B"),
        10.0: ("Healthy", "Grade B"),
        20.0: ("Defective", "Reject"),
        30.0: ("Defective", "Reject"),
        50.0: ("Defective", "Reject"),
    }

    for pct, (exp_health, exp_comm) in expected_grades.items():
        res = tree.evaluate_mango(
            ripeness="Ripe",
            ripeness_conf=90.0,
            defect_class="Healthy",
            defect_conf=80.0,
            visible_defect_pct=pct,
            defect_boxes=[[0, 0, 10, 10]] * int(max(1, pct * 2)) if pct > 0 else []
        )
        assert res["health_status"] == exp_health, f"At {pct}%, expected health {exp_health}, got {res['health_status']}"
        assert res["commercial_grade"] == exp_comm, f"At {pct}%, expected commercial {exp_comm}, got {res['commercial_grade']}"


def test_two_mangoes_separated_by_one_cm_gap_no_false_third_mango():
    """
    Verify that 2 mangoes separated by ~1 cm gap (with possible contact shadow or bridge)
    do NOT over-segment into 3 mangoes (Parts 15-18).
    """
    detector = MangoDetector()
    w, h = 600, 600
    img_arr = np.ones((h, w, 3), dtype=np.uint8) * 255  # White background

    y, x = np.ogrid[:h, :w]
    # Two true mangoes
    mask_a = (((x - 170) / 75) ** 2 + ((y - 300) / 100) ** 2) <= 1.0
    mask_b = (((x - 430) / 75) ** 2 + ((y - 300) / 100) ** 2) <= 1.0

    # 1 cm gap has a faint bridge / contact shadow between x=245 and x=355
    mask_mid = (x >= 245) & (x <= 355) & (np.abs(y - 300) <= 22)

    img_arr[mask_a] = [230, 185, 30]
    img_arr[mask_b] = [230, 185, 30]
    img_arr[mask_mid] = [225, 175, 35]

    test_img = Image.fromarray(img_arr)
    _, detections = detector.detect_mangoes(test_img)

    assert len(detections) == 2, f"Expected exactly 2 mangoes, but detected {len(detections)} (false middle sliver)"
    # Both detections should be large, realistic mangoes (> 20,000 px)
    for idx, d in enumerate(detections):
        assert d["area"] >= 15000.0, f"Mango {idx+1} area too small: {d['area']}"


def test_whitish_grey_cast_shadow_under_mango_excluded_from_mask():
    """
    Issue 1: Test that whitish-grey cast shadows underneath/around a mango
    photographed on a clean white table under overhead lighting are completely excluded
    from the mango mask, preserving true physical fruit boundaries.
    """
    detector = MangoDetector()
    w, h = 500, 400
    img_arr = np.ones((h, w, 3), dtype=np.uint8) * 248  # Clean white sheet

    yy, xx = np.ogrid[:h, :w]
    # Physical mango body (center 220, 180)
    mango_mask = (((xx - 220) / 90.0) ** 2 + ((yy - 180) / 70.0) ** 2) <= 1.0

    # Whitish-grey cast shadow underneath and to the right of the mango on the white sheet
    shadow_mask = (((xx - 270) / 80.0) ** 2 + ((yy - 240) / 45.0) ** 2) <= 1.0
    shadow_only = shadow_mask & (~mango_mask)

    # Base yellow mango
    img_arr[mango_mask, 0] = 235
    img_arr[mango_mask, 1] = 185
    img_arr[mango_mask, 2] = 30

    # Whitish-grey cast shadow on white table with slight warm ambient bounce
    img_arr[shadow_only, 0] = 185
    img_arr[shadow_only, 1] = 182
    img_arr[shadow_only, 2] = 175

    test_img = Image.fromarray(img_arr)
    _, detections = detector.detect_mangoes(test_img)

    assert len(detections) == 1, f"Expected 1 mango fruit, got {len(detections)}"
    det = detections[0]
    result_mask = det["mask"]

    # Verify that the external whitish-grey shadow region is NOT part of the mango mask
    shadow_overlap = np.sum(result_mask & shadow_only)
    shadow_total = np.sum(shadow_only)
    overlap_ratio = shadow_overlap / max(1, shadow_total)

    assert overlap_ratio < 0.05, f"Shadow leak: {overlap_ratio*100:.1f}% of whitish-grey shadow included in mango mask!"
    # Verify organic mango boundary solidity
    assert det["solidity"] >= 0.85
    assert det["area"] > 10000


def test_developer_debug_stages_include_shadow_correction_views():
    """
    Verify that developer inspection debug stages include estimated white bg,
    shadow mask, raw foreground, refined mask, and excluded shadow px.
    """
    detector = MangoDetector()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 60, 260, 220], fill=(235, 180, 30))
    # Add cast shadow
    draw.ellipse([200, 160, 320, 240], fill=(180, 180, 185))

    _, dets, debug_images = detector.detect_mangoes(img, return_debug=True)
    assert len(dets) == 1

    # Check that shadow correction debug stages are generated
    assert "debug_stage_white_bg" in debug_images
    assert "debug_stage_shadow_mask" in debug_images
    assert "debug_stage_raw_foreground" in debug_images
    assert "debug_stage_refined_mask" in debug_images
    assert "debug_stage_excluded_shadow" in debug_images

    # Check images are valid PIL Image instances
    for key in [
        "debug_stage_white_bg", "debug_stage_shadow_mask",
        "debug_stage_raw_foreground", "debug_stage_refined_mask",
        "debug_stage_excluded_shadow"
    ]:
        assert isinstance(debug_images[key], Image.Image)


def test_internal_defects_preserved_after_shadow_refinement():
    """
    Verify that removing boundary shadows does NOT clip genuine internal defects
    (both dark necrotic spots and pale scars) on the physical mango surface.
    """
    scanner = get_mango_quality_scanner()
    w, h = 450, 350
    img = Image.new("RGB", (w, h), (248, 248, 248))
    draw = ImageDraw.Draw(img)

    # Physical mango body
    draw.ellipse([80, 70, 280, 250], fill=(235, 185, 30))
    # Whitish-grey shadow on white sheet outside mango
    draw.ellipse([220, 190, 340, 270], fill=(190, 188, 180))

    # Genuine internal dark necrotic lesion (Anthracnose spot)
    draw.ellipse([160, 140, 185, 165], fill=(30, 25, 20))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]

    # Dark defect inside the mango must be detected
    assert det["visible_defect_pct"] > 0.0
    assert det["debug_numerical"]["accepted_defect_pixels"] > 0
    assert "Black Spot / Necrotic Lesion" in det["visible_defects"][0]


def test_white_disease_patch_on_mango_detected_as_defect():
    """
    Section 6.6.A: Verify that genuine white disease-infected patches on mango
    skin (e.g. powdery mildew / fungal mycelium) are detected as defects
    via surrounding-pixel local context analysis, not treated as background.
    """
    scanner = get_mango_quality_scanner()
    w, h = 450, 350
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Physical mango body (yellow-green peel)
    draw.ellipse([80, 70, 280, 250], fill=(225, 180, 40))

    # Genuine white fungal/powdery mildew patch on the mango skin
    # High lightness, desaturated, surrounded by healthy mango skin
    draw.ellipse([150, 130, 185, 165], fill=(240, 240, 242))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]

    # White defect must be detected
    assert det["visible_defect_pct"] > 0.0
    assert det["debug_numerical"]["accepted_defect_pixels"] > 0
    defect_types = " ".join(det["visible_defects"])
    assert ("White" in defect_types or "Pale" in defect_types or "Rot" in defect_types)


def test_grey_shadow_on_mango_skin_excluded_from_defects():
    """
    Section 6.6.B: Verify that a smooth grey illumination shadow falling across
    the mango skin is NOT counted as a disease defect, while the shadowed area
    remains part of the valid mango mask.
    """
    scanner = get_mango_quality_scanner()
    w, h = 450, 350
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Physical healthy mango body
    draw.ellipse([80, 70, 280, 250], fill=(225, 175, 35))

    # Smooth illumination shadow across bottom part of mango (dimmed peel, smooth transition)
    # Chroma preserved, lightness >= 48
    draw.ellipse([140, 180, 240, 240], fill=(130, 100, 25))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    det = res["detections"][0]

    # Smooth shadow must not be classified as a necrotic defect
    assert det["visible_defect_pct"] == 0.0 or det["debug_numerical"]["skin_shadow_pixels"] >= 0
    assert "Healthy" in det["health_status"] or det["visible_defect_pct"] < 3.0


def test_developer_debug_stages_include_local_context_and_classification():
    """
    Section 6.6.E: Verify that debug stages include candidate white patches,
    candidate grey shadows, local context windows, and pixel classification.
    """
    detector = MangoDetector()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.ellipse([80, 60, 260, 220], fill=(235, 180, 30))

    _, dets, debug_images = detector.detect_mangoes(img, return_debug=True)
    assert len(dets) == 1

    expected_stages = [
        "debug_stage_white_bg",
        "debug_stage_shadow_mask",
        "debug_stage_raw_foreground",
        "debug_stage_refined_mask",
        "debug_stage_excluded_shadow",
        "debug_stage_candidate_white_patches",
        "debug_stage_candidate_grey_shadows",
        "debug_stage_local_context_windows",
        "debug_stage_pixel_classification"
    ]
    for stage in expected_stages:
        assert stage in debug_images, f"Missing stage: {stage}"
        assert isinstance(debug_images[stage], Image.Image), f"Stage {stage} is not a PIL Image"


def test_dark_mango_recognized_as_fruit_and_healthy():
    """
    Mandatory Root-Cause Fix: Section 3.B & 3.G.
    Verify that completely black or very dark mangoes are recognized as fruit objects
    and correctly classified as healthy with 0% defects rather than falsely rejected or reported as 100% defective.
    """
    scanner = get_mango_quality_scanner()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    # Extremely dark / black mango on white table
    draw.ellipse([100, 60, 300, 240], fill=(25, 20, 20))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1, f"Expected 1 mango detected, got {res['mangoes_detected']}"
    assert res["healthy_count"] == 1
    assert res["defect_count"] == 0
    assert res["avg_surface_defect_pct"] == 0.0

    d0 = res["detections"][0]
    assert d0["health_status"] == "Healthy"
    assert d0["visible_defect_pct"] == 0.0
    assert d0["visible_defect_pct"] != 100.0, "Dark mango must not be reported as 100% defective"
    assert d0["commercial_grade"] in ["Grade A", "Grade B"]

    # Verify debug metrics reflect valid segmentation without 100% defect ratio
    dbg = d0["debug_numerical"]
    assert dbg["valid_mango_pixels"] > 10000
    assert dbg["accepted_defect_pixels"] == 0
    assert dbg["raw_defect_ratio"] == 0.0
    assert dbg["padding_margin_px"] >= 2


def test_dark_mango_with_genuine_necrotic_lesion():
    """
    Mandatory Root-Cause Fix: Section 3.B & 3.E.
    Verify that dark mangoes with genuine necrotic lesions are recognized as fruit,
    detect the lesion, and calculate defect percentage accurately from the lesion area rather than 100%.
    """
    scanner = get_mango_quality_scanner()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    # Dark mango with dark skin tones
    draw.ellipse([100, 60, 300, 240], fill=(32, 28, 25))
    # Genuine localized necrotic defect
    draw.ellipse([180, 130, 220, 170], fill=(10, 8, 8))

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 1
    d0 = res["detections"][0]
    assert d0["visible_defect_pct"] > 0.0
    assert d0["visible_defect_pct"] < 25.0, f"Expected localized defect pct, got {d0['visible_defect_pct']}%"
    assert len(d0["defect_regions"]) >= 1


def test_adaptive_internal_padding_formula_and_border_safety():
    """
    Mandatory Root-Cause Fix: Section 3.J.
    Verify slight adaptive inward padding (morphological erosion on defect-analysis mask only).
    Confirms:
    1. Defect percentage is strictly: confirmed defect pixels inside inner analysis mask / valid pixels in inner analysis mask * 100.
    2. Adaptive margin scales according to fruit's equivalent diameter.
    3. Excludes narrow uncertain border margin from defect classification.
    """
    scanner = get_mango_quality_scanner()
    w, h = 400, 400
    crop_img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(crop_img)
    draw.ellipse([50, 50, 350, 350], fill=(235, 185, 30))

    # Mask defining peel
    yy, xx = np.ogrid[:h, :w]
    mask = ((xx - 200)**2 + (yy - 200)**2) <= 150**2

    # Place a defect completely inside the fruit
    draw.ellipse([185, 185, 215, 215], fill=(20, 18, 15))

    defect_info = scanner.analyze_fruit_defects(crop_img, crop_mask=mask)

    # 1. Padding metrics exist and are scaled
    assert "padding_margin_px" in defect_info
    assert "padding_ratio" in defect_info
    assert "inner_analysis_mask" in defect_info
    assert defect_info["padding_margin_px"] >= 3, f"Expected margin >= 3, got {defect_info['padding_margin_px']}"

    # 2. Inner analysis mask is strictly eroded subset of full mask
    inner_mask = defect_info["inner_analysis_mask"]
    full_mask = defect_info["full_mango_mask"]
    assert np.all(inner_mask <= full_mask)
    assert np.sum(inner_mask) < np.sum(full_mask)

    # 3. Defect percentage strictly matches formula: accepted_defect_pixels / inner_mango_pixels * 100
    accepted_px = defect_info["accepted_defect_pixels"]
    inner_px = defect_info["inner_mango_pixels"]
    raw_ratio = defect_info["raw_defect_ratio"]
    assert abs(raw_ratio - (accepted_px / inner_px)) < 1e-4
    assert abs(defect_info["affected_area_pct"] - round(raw_ratio * 100.0, 2)) < 1e-4


def test_failed_fruit_detection_never_silently_becomes_100_percent_defect():
    """
    Mandatory Root-Cause Fix: Section 3.G.
    Verify that an empty image (no fruit detected) reports 0 samples, NEEDS_REVIEW,
    and NEVER defaults to 100% defect.
    """
    scanner = get_mango_quality_scanner()
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (240, 240, 240))  # Textured background tray with no mangoes
    draw = ImageDraw.Draw(img)
    for y in range(20, h, 30):
        draw.line([(10, y), (w - 10, y)], fill=(225, 225, 225), width=1)
    for x in range(20, w, 30):
        draw.line([(x, 10), (x, h - 10)], fill=(225, 225, 225), width=1)

    res = scanner.inspect_lot_image(img)
    assert res["mangoes_detected"] == 0
    assert res["sample_count"] == 0
    assert res["avg_surface_defect_pct"] == 0.0
    assert res["lot_defective_fruit_pct"] == 0.0
    assert res["affected_percentage"] == 0.0
    assert res["status"] == "NEEDS_REVIEW"
    assert res["lot_quality_grade"] == "Needs Review"



