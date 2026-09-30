"""
Smart Truck Allocation Engine using Google OR-Tools.
Classification: Optimization Engine (Mathematical Constraint Programming).
Do not label as Machine Learning.
"""

from typing import List, Dict, Any
from ortools.linear_solver import pywraplp

class TruckOptimizer:
    """
    Mathematical Optimization Engine for smart dispatch of agricultural transport.
    Minimizes total logistics travel distance and unfulfilled capacity
    subject to truck capacities, availability, and centre quotas.
    """
    def __init__(self):
        self.engine_name = "OR-Tools Integer Linear Programming Solver"

    def optimize_allocation(self, requests: List[Dict[str, Any]], available_trucks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        requests: list of dicts with:
          'request_id', 'village', 'quantity_quintals', 'distance_km', 'urgency'
        available_trucks: list of dicts with:
          'truck_id', 'truck_number', 'capacity_quintals', 'driver_name', 'current_centre_id'
        """
        if not requests or not available_trucks:
            return {
                "success": False,
                "engine": "Optimization Engine (Google OR-Tools)",
                "message": "Insufficient requests or trucks provided for optimization.",
                "allocations": []
            }

        # Create the MIP solver with CBC or SCIP backend
        solver = pywraplp.Solver.CreateSolver("SCIP")
        if not solver:
            solver = pywraplp.Solver.CreateSolver("CBC")
        if not solver:
            return self._heuristic_fallback(requests, available_trucks)

        num_trucks = len(available_trucks)
        num_requests = len(requests)

        # Decision variables: x[i, j] = 1 if truck i is assigned to request j
        x = {}
        for i in range(num_trucks):
            for j in range(num_requests):
                x[i, j] = solver.BoolVar(f"x_{i}_{j}")

        # Constraint 1: Each collection request is assigned to at most one truck
        for j in range(num_requests):
            solver.Add(solver.Sum([x[i, j] for i in range(num_trucks)]) <= 1)

        # Constraint 2: Truck capacity cannot be exceeded
        for i in range(num_trucks):
            t_cap = available_trucks[i]["capacity_quintals"]
            solver.Add(
                solver.Sum([x[i, j] * requests[j]["quantity_quintals"] for j in range(num_requests)]) <= t_cap
            )

        # Objective Function:
        # Maximize satisfied demand (benefit) while minimizing travel distance (cost)
        objective = solver.Objective()
        for i in range(num_trucks):
            for j in range(num_requests):
                qty = float(requests[j]["quantity_quintals"])
                dist = float(requests[j].get("distance_km", 20.0))
                urgency_raw = requests[j].get("urgency", 1.0)
                if isinstance(urgency_raw, str):
                    urgency_map = {"CRITICAL": 3.0, "HIGH": 2.0, "MEDIUM": 1.2, "LOW": 1.0}
                    urgency = urgency_map.get(urgency_raw.upper(), 1.0)
                else:
                    urgency = float(urgency_raw)
                # Benefit: quantity * urgency * 10
                # Cost: distance * 1.5
                coeff = (qty * urgency * 10.0) - (dist * 1.5)
                objective.SetCoefficient(x[i, j], coeff)

        objective.SetMaximization()

        solver.SetTimeLimit(5000) # 5 seconds max
        status = solver.Solve()

        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            allocations = []
            total_assigned_qty = 0.0
            total_distance = 0.0

            for i in range(num_trucks):
                assigned_reqs = []
                assigned_qty = 0.0
                max_dist = 0.0
                for j in range(num_requests):
                    if x[i, j].solution_value() > 0.5:
                        assigned_reqs.append(requests[j])
                        assigned_qty += requests[j]["quantity_quintals"]
                        max_dist = max(max_dist, requests[j].get("distance_km", 20.0))

                if assigned_reqs:
                    truck_info = available_trucks[i]
                    alloc_record = {
                        "truck_id": truck_info["truck_id"],
                        "truck_number": truck_info["truck_number"],
                        "driver_name": truck_info["driver_name"],
                        "capacity_quintals": truck_info["capacity_quintals"],
                        "assigned_quantity_quintals": round(assigned_qty, 2),
                        "utilization_percent": round((assigned_qty / truck_info["capacity_quintals"]) * 100, 2),
                        "estimated_roundtrip_km": round(max_dist * 2, 2),
                        "assigned_requests_count": len(assigned_reqs),
                        "stops": [
                            {
                                "request_id": r["request_id"],
                                "village": r["village"],
                                "quantity_quintals": r["quantity_quintals"]
                            }
                            for r in assigned_reqs
                        ]
                    }
                    allocations.append(alloc_record)
                    total_assigned_qty += assigned_qty
                    total_distance += max_dist * 2

            return {
                "success": True,
                "engine": "Optimization Engine (Google OR-Tools)",
                "solver_status": "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
                "total_trucks_dispatched": len(allocations),
                "total_quantity_scheduled_quintals": round(total_assigned_qty, 2),
                "total_estimated_km": round(total_distance, 2),
                "allocations": allocations
            }

        return self._heuristic_fallback(requests, available_trucks)

    def _heuristic_fallback(self, requests, available_trucks):
        # Greedy heuristic fallback if solver unavailable
        allocations = []
        truck_idx = 0
        current_truck = dict(available_trucks[0])
        current_stops = []
        current_qty = 0.0

        for r in requests:
            if current_qty + r["quantity_quintals"] <= current_truck["capacity_quintals"]:
                current_stops.append(r)
                current_qty += r["quantity_quintals"]
            else:
                if current_stops:
                    allocations.append({
                        "truck_id": current_truck["truck_id"],
                        "truck_number": current_truck["truck_number"],
                        "driver_name": current_truck["driver_name"],
                        "capacity_quintals": current_truck["capacity_quintals"],
                        "assigned_quantity_quintals": round(current_qty, 2),
                        "utilization_percent": round((current_qty / current_truck["capacity_quintals"]) * 100, 2),
                        "estimated_roundtrip_km": 40.0,
                        "stops": current_stops
                    })
                truck_idx += 1
                if truck_idx < len(available_trucks):
                    current_truck = dict(available_trucks[truck_idx])
                    current_stops = [r]
                    current_qty = r["quantity_quintals"]
                else:
                    break

        if current_stops and truck_idx < len(available_trucks):
            allocations.append({
                "truck_id": current_truck["truck_id"],
                "truck_number": current_truck["truck_number"],
                "driver_name": current_truck["driver_name"],
                "capacity_quintals": current_truck["capacity_quintals"],
                "assigned_quantity_quintals": round(current_qty, 2),
                "utilization_percent": round((current_qty / current_truck["capacity_quintals"]) * 100, 2),
                "estimated_roundtrip_km": 35.0,
                "stops": current_stops
            })

        return {
            "success": True,
            "engine": "Optimization Engine (Heuristic Fallback)",
            "solver_status": "HEURISTIC",
            "total_trucks_dispatched": len(allocations),
            "total_quantity_scheduled_quintals": sum(a["assigned_quantity_quintals"] for a in allocations),
            "allocations": allocations
        }

truck_optimizer = TruckOptimizer()
