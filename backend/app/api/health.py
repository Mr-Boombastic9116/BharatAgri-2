from fastapi import APIRouter
from backend.app.core.database import check_db_health
from ml.inference.supply_predictor import supply_predictor
from ml.inference.anomaly_detector import anomaly_detector

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    db_ok = check_db_health()
    ai_ok = supply_predictor.is_loaded and anomaly_detector.is_loaded

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "ai": "available" if ai_ok else "fallback_active",
        "version": "2.0.0",
        "timestamp": "2026-09-30T22:15:00Z"
    }
