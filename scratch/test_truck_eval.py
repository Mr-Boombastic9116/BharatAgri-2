from ml.inference.truck_optimizer import TruckOptimizer

optimizer = TruckOptimizer()

# Test sample collection requests
sample_requests = [
    {"request_id": "REQ-01", "village": "Canacona", "quantity_quintals": 45.0, "distance_km": 18.5, "urgency": "HIGH"},
    {"request_id": "REQ-02", "village": "Quepem", "quantity_quintals": 60.0, "distance_km": 24.0, "urgency": "MEDIUM"},
    {"request_id": "REQ-03", "village": "Sanguem", "quantity_quintals": 35.0, "distance_km": 32.0, "urgency": "LOW"},
    {"request_id": "REQ-04", "village": "Ponda", "quantity_quintals": 50.0, "distance_km": 15.0, "urgency": "HIGH"}
]

sample_trucks = [
    {"truck_id": "TRK-01", "truck_number": "GA-02-T-1100", "capacity_quintals": 100.0, "driver_name": "Suresh", "current_centre_id": "CENTRE-GOA-01"},
    {"truck_id": "TRK-02", "truck_number": "GA-02-T-2200", "capacity_quintals": 100.0, "driver_name": "Mahesh", "current_centre_id": "CENTRE-GOA-01"}
]

result = optimizer.optimize_allocation(sample_requests, sample_trucks)
print("Optimization Status:", result.get("success"))
print("Allocations Count:", len(result.get("allocations", [])))
print("Summary Metrics:")
for k, v in result.items():
    if k not in ["allocations", "message"]:
        print(f"  {k}: {v}")
