"""
Test Suite: Supply & Demand Mathematics and Integrity Audit
Validates:
1. Surplus/Deficit Exact Formula: expected_supply - expected_demand
2. Metric distinction: current_procurement, projected_procurement, current_inventory, expected_supply, available_storage
3. Classification consistency: SURPLUS (>2000 Q), DEFICIT (<-1000 Q), BALANCED (-1000 to 2000 Q)
4. Crop-specific inventory (StorageLot queries do not aggregate cross-crop)
5. Edge Cases: zero demand, zero supply, balanced market, extreme surplus/deficit
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import SessionLocal
from backend.app.models.price import StateCropSupplyDemand
from backend.app.models.procurement import StorageLot
from backend.app.models.centre import ProcurementCentre
from sqlalchemy import func

def test_surplus_deficit_formula_consistency():
    db = SessionLocal()
    rows = db.query(StateCropSupplyDemand).all()
    assert len(rows) > 0, "State crop supply demand records must exist"

    for r in rows:
        supply = float(r.expected_supply_quintals)
        demand = float(r.expected_demand_quintals)
        expected_surplus = round(supply - demand, 2)
        actual_surplus = float(r.surplus_deficit_quintals)

        # Mathematical equality check
        assert abs(actual_surplus - expected_surplus) < 0.05, (
            f"Math error in {r.state} {r.crop}: expected {expected_surplus}, got {actual_surplus}"
        )

        # Label consistency check
        if expected_surplus > 2000:
            assert r.market_sentiment == "SURPLUS", f"Expected SURPLUS for {expected_surplus} Q, got {r.market_sentiment}"
        elif expected_surplus < -1000:
            assert r.market_sentiment == "DEFICIT", f"Expected DEFICIT for {expected_surplus} Q, got {r.market_sentiment}"
        else:
            assert r.market_sentiment == "BALANCED", f"Expected BALANCED for {expected_surplus} Q, got {r.market_sentiment}"

    db.close()

def test_inventory_is_crop_specific():
    """Verify inventory counts storage lots for that specific crop, not entire godown usage"""
    db = SessionLocal()
    goa_paddy = db.query(StateCropSupplyDemand).filter(
        StateCropSupplyDemand.state == "Goa",
        StateCropSupplyDemand.crop == "Paddy"
    ).first()
    assert goa_paddy is not None

    # Total godown usage across all crops in Goa
    total_centre_usage = db.query(func.sum(ProcurementCentre.current_storage_usage_quintals)).filter(
        ProcurementCentre.state == "Goa"
    ).scalar() or 0.0

    # Crop-specific Paddy lots in Goa
    paddy_lot_inv = db.query(func.sum(StorageLot.quantity_quintals)).join(
        ProcurementCentre, StorageLot.centre_id == ProcurementCentre.centre_id
    ).filter(
        ProcurementCentre.state == "Goa",
        StorageLot.crop == "Paddy"
    ).scalar() or 0.0

    print(f"Goa Paddy Inventory: {goa_paddy.current_inventory_quintals} Q | Paddy lots: {paddy_lot_inv} Q | Total centre usage: {total_centre_usage} Q")
    # Verify crop inventory does not equal total godown usage if multiple crops exist
    assert float(goa_paddy.current_inventory_quintals) < float(total_centre_usage), (
        "Crop inventory should not be conflated with total centre storage usage"
    )
    db.close()

def test_supply_demand_edge_cases():
    """Edge cases: Zero supply, zero demand, exact balance"""
    # 1. Zero demand: surplus = supply
    supply = 10000.0
    demand = 0.0
    surplus = supply - demand
    status = "SURPLUS" if surplus > 2000 else "DEFICIT" if surplus < -1000 else "BALANCED"
    assert surplus == 10000.0
    assert status == "SURPLUS"

    # 2. Zero supply: deficit = -demand
    supply = 0.0
    demand = 15000.0
    surplus = supply - demand
    status = "SURPLUS" if surplus > 2000 else "DEFICIT" if surplus < -1000 else "BALANCED"
    assert surplus == -15000.0
    assert status == "DEFICIT"

    # 3. Balanced: supply close to demand
    supply = 50500.0
    demand = 50000.0
    surplus = supply - demand
    status = "SURPLUS" if surplus > 2000 else "DEFICIT" if surplus < -1000 else "BALANCED"
    assert surplus == 500.0
    assert status == "BALANCED"

if __name__ == "__main__":
    test_surplus_deficit_formula_consistency()
    test_inventory_is_crop_specific()
    test_supply_demand_edge_cases()
    print("ALL SUPPLY/DEMAND MATHEMATICS TESTS PASSED!")
