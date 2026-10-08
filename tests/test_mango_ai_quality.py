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




