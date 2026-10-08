import os
from sqlalchemy.orm import Session
from backend.app.core.database import engine
from backend.app.models.centre import ProcurementCentre, Employee

CENTRE_ROLES = [
    ("Intake Officer", "Ramesh Naik", "EMP-01"),
    ("QC Officer", "Sunita Patil", "EMP-02"),
    ("AI QC Lead", "Amit Desai", "EMP-03"),
    ("Weighbridge Op", "Vijay Gaonkar", "EMP-04"),
    ("Procurement Mgr", "Preeti Shinde", "EMP-05"),
    ("Storage Supervisor", "Prakash Rane", "EMP-06"),
]

MAHA_NAMES = [
    ("Intake Officer", "Sanjay Deshmukh", "EMP-01"),
    ("QC Officer", "Anjali Kulkarni", "EMP-02"),
    ("AI QC Lead", "Rohit Chavan", "EMP-03"),
    ("Weighbridge Op", "Ganesh More", "EMP-04"),
    ("Procurement Mgr", "Meena Jadhav", "EMP-05"),
    ("Storage Supervisor", "Dattatray Shinde", "EMP-06"),
]

KAR_NAMES = [
    ("Intake Officer", "Basavaraj Gowda", "EMP-01"),
    ("QC Officer", "Lakshmi Hegde", "EMP-02"),
    ("AI QC Lead", "Kiran Kumar", "EMP-03"),
    ("Weighbridge Op", "Manjunath Pujar", "EMP-04"),
    ("Procurement Mgr", "Shobha Patil", "EMP-05"),
    ("Storage Supervisor", "Shivakumar Reddy", "EMP-06"),
]

def seed_employees():
    with Session(engine) as db:
        centres = db.query(ProcurementCentre).all()
        total_seeded = 0
        for c in centres:
            state = c.state or "Goa"
            if state == "Maharashtra":
                template = MAHA_NAMES
            elif state == "Karnataka":
                template = KAR_NAMES
            else:
                template = CENTRE_ROLES

            for role, base_name, code_suffix in template:
                code = f"{c.centre_id}-{code_suffix}"
                existing = db.query(Employee).filter(
                    Employee.centre_id == c.centre_id,
                    Employee.employee_code == code
                ).first()
                if not existing:
                    emp = Employee(
                        centre_id=c.centre_id,
                        name=f"{base_name} ({role})",
                        role=role,
                        employee_code=code,
                        phone="9876543210",
                        email=f"{code.lower()}@bharatagri.gov.in",
                        status="ACTIVE"
                    )
                    db.add(emp)
                    total_seeded += 1
        db.commit()
        print(f"Successfully seeded {total_seeded} employees across {len(centres)} centres!")

if __name__ == "__main__":
    seed_employees()
