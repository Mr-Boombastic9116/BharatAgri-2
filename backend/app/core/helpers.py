from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from backend.app.models.centre import ProcurementCentre
from backend.app.models.farmer import Farmer
from backend.app.models.user import User

def resolve_centre(centre_id_or_uid: str, db: Session) -> Optional[ProcurementCentre]:
    if not centre_id_or_uid:
        return None
    cid = str(centre_id_or_uid).strip()

    # 1. Exact match on centre_id
    c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == cid).first()
    if c:
        return c

    # 2. Match on integer id
    c = db.query(ProcurementCentre).filter(cast(ProcurementCentre.id, String) == cid).first()
    if c:
        return c

    # 3. Match user by user_id or email
    u = db.query(User).filter((User.user_id == cid) | (User.email == cid)).first()
    if u and getattr(u, 'centre_id', None):
        c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == u.centre_id).first()
        if c:
            return c

    # 4. Fallback for demo centre manager
    if "centre" in cid.lower():
        c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == "CENTRE-GOA-01").first()
        if c:
            return c

    # 5. Default first operational centre
    return db.query(ProcurementCentre).first()


def resolve_farmer(farmer_id_or_uid: str, db: Session) -> Optional[Farmer]:
    if not farmer_id_or_uid:
        return None
    fid = str(farmer_id_or_uid).strip()

    # 1. Match by user_id
    f = db.query(Farmer).filter(Farmer.user_id == fid).first()
    if f:
        return f

    # 2. Match by farmer_code
    f = db.query(Farmer).filter(Farmer.farmer_code == fid).first()
    if f:
        return f

    # 3. Match by numeric id
    f = db.query(Farmer).filter(cast(Farmer.id, String) == fid).first()
    if f:
        return f

    # 4. Fallback for demo farmer
    if "farmer" in fid.lower():
        f = db.query(Farmer).filter(Farmer.user_id == "farmer@bharatagri.demo").first()
        if f:
            return f

    return None
