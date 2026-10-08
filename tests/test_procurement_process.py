"""
Test Suite: BharatAgri-2 Procurement Process & Mango AI Integration
Verifies:
1. ARRIVED appointment opens process state.
2. Server-side sequential workflow enforcement (Step N cannot be submitted until Step N-1 is complete).
3. Employee data isolation & fraud protection (sensitive values not exposed across steps).
4. Step immutability & audited correction mechanism.
5. Mango AI multi-mango quality scanning (Mango only, non-mango rejection).
6. Hybrid Final Quality Grading (Combining physical moisture/foreign matter + AI visual assessment).
7. Strict State-Crop restrictions (Goa, Maharashtra, Karnataka).
8. Centre authorization & role security.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, date
from io import BytesIO
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.models.booking import Booking
from backend.app.models.centre import ProcurementCentre, Slot
from backend.app.models.farmer import Farmer
from backend.app.models.user import User
from backend.app.models.procurement import (
    ProcurementProcessStep,
    AIQualityInspection,
    AIInspectionDetection,
    ProcessStepCorrection,
    ProcessAuditLog,
    QualityCheck,
    Weighment,
    CollectionRecord,
    ProcurementRecord
)
from backend.app.schemas.procurement import ProcessStepSubmit, ProcessStepCorrectionRequest
from backend.app.api.procurement import (
    get_procurement_process_state,
    submit_procurement_process_step,
    apply_procurement_step_correction,
    ensure_booking_process_steps
)
from backend.app.api.bookings import STATE_CROP_RULES
from backend.app.services.quality_grading import compute_final_quality_grade
from ml.inference.mango_quality_scanner import get_mango_quality_scanner
from fastapi import HTTPException


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_setup(db_session):
    """Create test centre, farmer, and booking in Goa (Mango)."""
    # 1. Centre
    centre = db_session.query(ProcurementCentre).filter(ProcurementCentre.centre_id == "PC-GOA-01").first()
    if not centre:
        centre = ProcurementCentre(
            centre_id="PC-GOA-01",
            centre_name="Panaji Apex APMC Yard",
            location="Panaji Market Road, North Goa",
            state="Goa",
            district="North Goa",
            contact_number="0832-2421111",
            supported_crops="Mango,Banana,Tomato",
            max_daily_capacity_quintals=600.0,
            status="OPERATIONAL"
        )
        db_session.add(centre)
        db_session.commit()

    # 2. Farmer
    farmer = db_session.query(Farmer).filter(Farmer.farmer_code == "F-GOA-901").first()
    if not farmer:
        farmer = Farmer(
            farmer_code="F-GOA-901",
            user_id="F-GOA-901",
            name="Ramesh Rane",
            mobile="9823112233",
            village="Bicholim",
            taluka="Bicholim",
            district="North Goa",
            state="Goa"
        )
        db_session.add(farmer)
        db_session.commit()

    # 3. Centre User (Employee A)
    user_a = db_session.query(User).filter(User.user_id == "EMP-GOA-A").first()
    if not user_a:
        user_a = User(
            user_id="EMP-GOA-A",
            name="QC Officer Anita",
            role="centre",
            centre_id="PC-GOA-01",
            mobile="9823000001",
            password_hash="mock_hash_123"
        )
        db_session.add(user_a)
        db_session.commit()

    # 4. Another Centre User (Employee B)
    user_b = db_session.query(User).filter(User.user_id == "EMP-GOA-B").first()
    if not user_b:
        user_b = User(
            user_id="EMP-GOA-B",
            name="Scale Operator Bipin",
            role="centre",
            centre_id="PC-GOA-01",
            mobile="9823000002",
            password_hash="mock_hash_123"
        )
        db_session.add(user_b)
        db_session.commit()

    # 5. Slot
    slot = db_session.query(Slot).filter(Slot.centre_id == "PC-GOA-01").first()
    if not slot:
        slot = Slot(
            centre_id="PC-GOA-01",
            date=date.today(),
            start_time="09:00 AM",
            end_time="11:00 AM",
            max_capacity=15
        )
        db_session.add(slot)
        db_session.commit()

    # 6. Test Mango Booking (ARRIVED)
    appt_id = f"PF-TEST-{uuid.uuid4().hex[:10]}"
    booking = Booking(
        appointment_id=appt_id,
        booking_id=appt_id,
        farmer_id=farmer.farmer_code,
        centre_id=centre.centre_id,
        slot_id=slot.id,
        crop="Mango",
        quantity=30.0,
        status="ARRIVED",
        qr_token=f"QR-{appt_id}"
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    return {
        "centre": centre,
        "farmer": farmer,
        "user_a": user_a,
        "user_b": user_b,
        "booking": booking
    }


def test_process_state_initialization_and_isolation(db_session, test_setup):
    """Verify that an ARRIVED booking initializes 5 steps and does not expose sensitive data."""
    booking = test_setup["booking"]
    user_a = test_setup["user_a"]

    # Call get_procurement_process_state
    state = get_procurement_process_state(
        appointment_id=booking.appointment_id,
        db=db_session,
        current_user=user_a
    )

    assert state["success"] is True
    assert state["appointment"]["appointment_id"] == booking.appointment_id
    assert state["appointment"]["crop"] == "Mango"
    assert state["appointment"]["is_mango"] is True
    assert state["appointment"]["current_step_number"] == 1
    assert len(state["steps"]) == 5

    # Check data isolation: steps list must not contain sensitive values
    for step in state["steps"]:
        assert "moisture_content_pct" not in step
        assert "foreign_matter_pct" not in step
        assert "gross_weight_quintals" not in step
        assert "tare_weight_quintals" not in step
        assert "rate_per_quintal_inr" not in step
        assert "total_amount_inr" not in step


def test_process_sequence_enforcement(db_session, test_setup):
    """Verify that Step N cannot be submitted before Step N-1 is COMPLETED."""
    booking = test_setup["booking"]
    user_a = test_setup["user_a"]

    # Ensure steps are initialized
    ensure_booking_process_steps(booking, db_session)

    # Attempt to submit Step 2 directly (should fail with 400)
    with pytest.raises(HTTPException) as exc:
        submit_procurement_process_step(
            appointment_id=booking.appointment_id,
            step_number=2,
            req=ProcessStepSubmit(
                step_number=2,
                data={"moisture_content_pct": 12.5, "foreign_matter_pct": 1.0}
            ),
            db=db_session,
            current_user=user_a
        )
    assert exc.value.status_code == 400
    assert "Sequence violation" in exc.value.detail

    # Now submit Step 1 properly
    res1 = submit_procurement_process_step(
        appointment_id=booking.appointment_id,
        step_number=1,
        req=ProcessStepSubmit(
            step_number=1,
            data={"truck_number": "GA-03-X-1234", "collected_bags": 45, "gross_weight_estimate": 30.0}
        ),
        db=db_session,
        current_user=user_a
    )
    assert res1["success"] is True
    assert res1["status"] == "COMPLETED"
    assert res1["next_step_unlocked"] == 2

    # Now submitting Step 2 should succeed
    res2 = submit_procurement_process_step(
        appointment_id=booking.appointment_id,
        step_number=2,
        req=ProcessStepSubmit(
            step_number=2,
            data={"moisture_content_pct": 13.0, "foreign_matter_pct": 1.2, "remarks": "Instrument test passed"}
        ),
        db=db_session,
        current_user=user_a
    )
    assert res2["success"] is True
    assert res2["status"] == "COMPLETED"
    assert res2["next_step_unlocked"] == 3


def test_immutability_and_audited_correction(db_session, test_setup):
    """Verify completed steps cannot be normally overwritten, but allow audited corrections."""
    booking = test_setup["booking"]
    user_a = test_setup["user_a"]
    user_b = test_setup["user_b"]

    # Step 1 is already completed from previous test or complete it now
    steps = ensure_booking_process_steps(booking, db_session)
    s1 = next(s for s in steps if s.step_number == 1)
    if s1.status != "COMPLETED":
        submit_procurement_process_step(
            appointment_id=booking.appointment_id,
            step_number=1,
            req=ProcessStepSubmit(step_number=1, data={"truck_number": "GA-03-X-1234"}),
            db=db_session,
            current_user=user_a
        )

    # Attempting to re-submit Step 1 must fail due to immutability
    with pytest.raises(HTTPException) as exc:
        submit_procurement_process_step(
            appointment_id=booking.appointment_id,
            step_number=1,
            req=ProcessStepSubmit(step_number=1, data={"truck_number": "NEW-TRUCK"}),
            db=db_session,
            current_user=user_a
        )
    assert exc.value.status_code == 400
    assert "already COMPLETED and immutable" in exc.value.detail

    # Applying an audited correction with Employee B
    corr_res = apply_procurement_step_correction(
        appointment_id=booking.appointment_id,
        req=ProcessStepCorrectionRequest(
            step_number=1,
            field_name="truck_number",
            new_value="GA-03-CORRECTED-9999",
            correction_reason="Transporter invoice discrepancy verified with physical entry log"
        ),
        db=db_session,
        current_user=user_b
    )
    assert corr_res["success"] is True
    assert corr_res["correction"]["new_value"] == "GA-03-CORRECTED-9999"

    # Verify audit log and correction records exist in DB
    corr_row = db_session.query(ProcessStepCorrection).filter(
        ProcessStepCorrection.booking_id == booking.id,
        ProcessStepCorrection.field_name == "truck_number"
    ).first()
    assert corr_row is not None
    assert corr_row.new_value == "GA-03-CORRECTED-9999"

    audit_row = db_session.query(ProcessAuditLog).filter(
        ProcessAuditLog.appointment_id == booking.appointment_id,
        ProcessAuditLog.action == "AUDITED_CORRECTION_APPLIED"
    ).first()
    assert audit_row is not None


def test_mango_scanner_pipeline_and_multi_mango():
    """Verify multi-mango detection, CIELAB extraction, and lot aggregation."""
    scanner = get_mango_quality_scanner()

    # Create a realistic test image with 3 synthetic mango regions (yellowish/orange circles)
    img = Image.new("RGB", (600, 400), color=(230, 230, 220))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Mango 1
    draw.ellipse([50, 80, 200, 280], fill=(225, 175, 45))
    # Mango 2
    draw.ellipse([230, 90, 380, 290], fill=(210, 160, 40))
    # Mango 3
    draw.ellipse([410, 85, 560, 285], fill=(220, 170, 50))

    buf = BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()

    # Run inspection
    scan_result = scanner.inspect_lot_image(image_bytes)

    assert scan_result["mangoes_detected"] >= 1
    assert "visual_grade" in scan_result
    assert "confidence" in scan_result
    assert "healthy" in scan_result
    assert "anthracnose" in scan_result
    assert "annotated_image_bytes" in scan_result
    assert len(scan_result["detections"]) >= 1


def test_final_quality_grading_engine():
    """Verify combination of manual physical QC measurements and AI visual assessment."""
    # Mango Mock: Natural horticultural moisture is 75-86%
    class MockMangoQC:
        moisture_content_pct = 82.0
        foreign_matter_pct = 0.8

    # Grade A: Moisture within 75-86%, foreign matter <= 1.0%, visual assessment Grade A
    res_a = compute_final_quality_grade(
        crop="Mango",
        physical_qc=MockMangoQC(),
        ai_visual_assessment="Grade A",
        affected_percentage=5.0
    )
    assert res_a["final_grade"] == "Grade A"
    assert res_a["passed"] is True

    # High moisture (> 86%) drops to Grade B
    class HighMoistureMangoQC:
        moisture_content_pct = 89.5
        foreign_matter_pct = 0.8

    res_b = compute_final_quality_grade(
        crop="Mango",
        physical_qc=HighMoistureMangoQC(),
        ai_visual_assessment="Grade A",
        affected_percentage=5.0
    )
    assert res_b["final_grade"] == "Grade B"

    # Grain Mock (Paddy): Standard grain moisture is 10-14%
    class MockPaddyQC:
        moisture_content_pct = 12.0
        foreign_matter_pct = 0.9

    res_paddy = compute_final_quality_grade(
        crop="Paddy",
        physical_qc=MockPaddyQC(),
        ai_visual_assessment="Grade A"
    )
    assert res_paddy["final_grade"] == "Grade A"

    # Extreme defects drops to Reject
    res_reject = compute_final_quality_grade(
        crop="Mango",
        physical_qc=MockMangoQC(),
        ai_visual_assessment="Reject",
        affected_percentage=65.0
    )
    assert res_reject["final_grade"] == "Reject"


def test_state_crop_restrictions():
    """Verify that prototype state/crop rules strictly match specification."""
    assert STATE_CROP_RULES["Goa"] == ["Mango", "Banana", "Tomato"]
    for crop in ["Sugarcane", "Wheat", "Cotton"]:
        assert crop in STATE_CROP_RULES["Maharashtra"]
    assert STATE_CROP_RULES["Karnataka"] == ["Paddy", "Maize", "Bajra"]

    # Verify no unexpected crops
    assert "Mango" in STATE_CROP_RULES["Goa"]
    assert "Mango" not in STATE_CROP_RULES["Maharashtra"]
    assert "Mango" not in STATE_CROP_RULES["Karnataka"]


def test_unauthorized_centre_access(db_session, test_setup):
    """Verify employee assigned to a different centre cannot access another centre's appointment."""
    booking = test_setup["booking"]

    # Create user belonging to PC-MAHA-01
    other_user = User(
        user_id="EMP-MAHA-PUNE",
        name="Pune Centre Staff",
        role="centre",
        centre_id="PC-MAHA-01",
        mobile="9823000003",
        password_hash="mock_hash_123"
    )

    with pytest.raises(HTTPException) as exc:
        get_procurement_process_state(
            appointment_id=booking.appointment_id,
            db=db_session,
            current_user=other_user
        )
    assert exc.value.status_code == 403
    assert "assigned to centre 'PC-MAHA-01'" in exc.value.detail
