import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.app.core.database import SessionLocal
from backend.app.api.procurement import get_traceability_lot

db = SessionLocal()
try:
    print("Testing PF-260930-101:")
    res1 = get_traceability_lot("PF-260930-101", db)
    print("Found for PF-260930-101:", res1["lot_id"])
except Exception as e:
    print("Failed for PF-260930-101:", e)

try:
    print("Testing booking id 1:")
    res2 = get_traceability_lot("1", db)
    print("Found for 1:", res2["lot_id"])
except Exception as e:
    print("Failed for 1:", e)

try:
    print("Testing LOT-2026-GO-CENTRE-GOA-01-007866:")
    res3 = get_traceability_lot("LOT-2026-GO-CENTRE-GOA-01-007866", db)
    print("Found for LOT-2026-GO-CENTRE-GOA-01-007866:", res3["lot_id"])
except Exception as e:
    print("Failed for lot_id:", e)

try:
    print("Testing booking 10202:")
    res4 = get_traceability_lot("10202", db)
    print("Found for 10202:", res4["lot_id"])
except Exception as e:
    print("Failed for 10202:", e)

db.close()
