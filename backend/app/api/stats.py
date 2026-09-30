from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.farmer import Farmer
from backend.app.models.centre import ProcurementCentre
from backend.app.models.booking import Booking

router = APIRouter(tags=["Public Statistics"])

@router.get("/api/stats")
def get_public_stats(db: Session = Depends(get_db)):
    farmers_count = db.query(func.count(Farmer.id)).scalar() or 0
    centres_count = db.query(func.count(ProcurementCentre.id)).scalar() or 0
    bookings_count = db.query(func.count(Booking.id)).scalar() or 0

    return {
        "farmers_registered": farmers_count,
        "procurement_centres": centres_count,
        "slots_managed": bookings_count
    }
