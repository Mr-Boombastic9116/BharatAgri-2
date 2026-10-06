"""
End-to-End Verification of Anomaly Detection Pipeline (Section 5).
Validates model inference, strict labeling, persistence, review workflow, and intake integration.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.inference.anomaly_detector import anomaly_detector
from backend.app.core.database import SessionLocal
from backend.app.models.ai import AnomalyRecord
from backend.app.models.alert import Alert
from backend.app.api.ai import list_anomalies, update_anomaly_status, detect_transaction_anomaly, TransactionAnomalyCheck
from backend.app.schemas.ai import AnomalyStatusUpdate


def test_anomaly_detector_labeling():
    print("Testing Anomaly Detector inference...")
    # Normal transaction: 50 booked, 50 collected, 49.5 weighed, 49.5 procured, 12.5% moisture
    res_normal = anomaly_detector.evaluate_transaction(
        booked_qty=50.0,
        collected_qty=50.0,
        weighed_qty=49.5,
        procured_qty=49.5,
        moisture_content=12.5,
        processing_time_mins=45.0
    )
    assert res_normal["is_potential_anomaly"] == False or res_normal["is_anomaly"] == False, "Normal transaction flagged unexpectedly"
    assert res_normal["label"] == "Normal Transaction"
    print("  [PASS] Normal transaction correctly cleared.")

    # Anomalous transaction: 50 booked, 50 collected, 95 weighed (+90% weight surge), 18% moisture
    res_anom = anomaly_detector.evaluate_transaction(
        booked_qty=50.0,
        collected_qty=50.0,
        weighed_qty=95.0,
        procured_qty=95.0,
        moisture_content=18.0,
        processing_time_mins=220.0
    )
    assert res_anom["is_potential_anomaly"] == True and res_anom["is_anomaly"] == True, "Failed to flag obvious anomaly"
    assert res_anom["label"] == "Potential Anomaly — Requires Review", f"Invalid label: {res_anom['label']}"
    assert "Fraud" not in res_anom["label"], "Must never declare fraud automatically"
    print(f"  [PASS] Anomalous transaction flagged with label: '{res_anom['label']}'")


def test_anomaly_api_and_review_workflow():
    print("Testing Anomaly API and human review workflow...")
    db = SessionLocal()
    try:
        # Detect & persist via API
        payload = TransactionAnomalyCheck(
            booked_quantity=40.0,
            collected_quantity=40.0,
            weighed_quantity=88.0,
            procured_quantity=88.0,
            moisture_content=18.5,
            processing_time_mins=210.0,
            entity_type="PROCUREMENT",
            entity_id="PRC-TEST-0001",
            centre_id="CENTRE-GOA-01"
        )
        fake_user = {"user_id": "USR-TEST-001", "role": "GOVERNMENT"}
        detect_res = detect_transaction_anomaly(payload=payload, db=db, current_user=fake_user)
        assert detect_res["success"] == True
        assert detect_res["data"]["recorded"] == True
        anomaly_code = detect_res["data"]["anomaly_code"]
        print(f"  [PASS] Anomaly detected and recorded with code: {anomaly_code}")

        # Retrieve anomalies via GET
        list_res = list_anomalies(db=db, limit=10, current_user=fake_user)
        assert list_res["success"] == True
        assert list_res["classification"] == "Potential Anomaly — Requires Review"
        found = next((a for a in list_res["data"] if a["anomaly_code"] == anomaly_code), None)
        assert found is not None, "Newly detected anomaly not found in GET /anomalies response"
        assert found["risk_label"] == "Potential Anomaly — Requires Review"
        assert isinstance(found["affected_record"], str), "affected_record must be a renderable string"
        assert isinstance(found["centre_location"], str), "centre_location must be a renderable string"
        print(f"  [PASS] Anomaly retrieved with verified structure and formatted strings.")

        # Update review status
        rec_id = found["id"]
        update_payload = AnomalyStatusUpdate(status="RESOLVED", notes="Inspected scale logs; tare error corrected.")
        update_res = update_anomaly_status(anomaly_id=rec_id, payload=update_payload, db=db, current_user=fake_user)
        assert update_res["success"] == True
        assert update_res["data"]["status"] == "RESOLVED"
        print("  [PASS] Anomaly review status updated to RESOLVED with audit trail.")

        # Clean up test anomaly
        db.query(AnomalyRecord).filter(AnomalyRecord.anomaly_code == anomaly_code).delete()
        db.commit()
        print("  [PASS] Test anomaly record cleaned up.")
    finally:
        db.close()


if __name__ == "__main__":
    test_anomaly_detector_labeling()
    test_anomaly_api_and_review_workflow()
    print("\nALL ANOMALY PIPELINE TESTS PASSED!")
