# Procurement Process Security & Employee Data Isolation

BharatAgri-2 implements a sequential, role-segregated 5-step procurement process designed to eliminate employee fraud, collusion, and confirmation bias during intake operations.

---

## 1. 5-Step Sequential Workflow

When an appointment achieves `ARRIVED` status, the centre employee navigates to:
`/centre/appointments/{appointmentId}/process`

The processing sequence consists of five strict phases:
1. **Step 1: Arrival Verification & Lot Collection**: Vehicle inspection, gross intake estimate, physical container count.
2. **Step 2: Physical Quality Inspection**: Instrument-based measurements (Moisture %, Foreign Matter %, physical observations).
3. **Step 3: AI Visual Quality Inspection**: Multi-mango photographic scan for defect classification (or manual visual check for other crops).
4. **Step 4: Weighment**: Certified weighbridge gross weight and tare weight determination.
5. **Step 5: Procurement Finalization**: Algorithmic grade fusion, MSP calculation, payment creation, and lot locking.

---

## 2. Server-Side Sequence Enforcement

Sequence progression is enforced unconditionally on the backend in `backend/app/api/procurement.py`:
- `Step N+1` is in `LOCKED` status until `Step N` achieves `COMPLETED` status.
- Attempting to submit `Step N+1` prior to `Step N` raises HTTP `400 Bad Request`:
  `"Cannot submit Step X. Preceding step (X-1) must be COMPLETED first."`
- Once a step is `COMPLETED`, direct overwrites are blocked. Any attempt to re-submit raises HTTP `400 Bad Request`:
  `"Step X is already COMPLETED and is immutable. Use the audited correction mechanism if revisions are required."`

---

## 3. Strict Employee Data Isolation (Fraud Prevention)

In conventional mandi setups, downstream workers often replicate numbers entered by upstream peers (e.g., weighbridge operators rounding net weight to match the intake receipt, or payment clerks adjusting rates based on previous inspector notes).

BharatAgri-2 prevents this through strict field-level sanitization:

### Information Hiding Rules:
- When a user calls `GET /api/procurement/process/{appointment_id}/state`, the API checks the currently active step.
- Sensitive values entered in previous steps are **stripped from the response payload**:
  - `moisture_content_pct`
  - `foreign_matter_pct`
  - `gross_weight_quintals`
  - `tare_weight_quintals`
  - `net_weight_quintals`
  - `rate_per_quintal_inr`
  - `total_procurement_value`
- Downstream employees see only permitted operational metadata:
  ```json
  {
    "step_number": 2,
    "step_type": "PHYSICAL_QUALITY_INSPECTION",
    "status": "COMPLETED",
    "completed_by": "USR-QC-01",
    "employee_name": "QC Officer Anita",
    "completed_at": "2026-10-06T15:30:00Z"
  }
  ```
- Sensitive figures are **never** rendered into hidden inputs, DOM attributes, localStorage, or client JavaScript state.

---

## 4. Controlled Audited Corrections

If an honest clerical mistake occurs in a completed step, silent database overwrites are prohibited. The authorized user must submit an audited correction via:

`POST /api/procurement/process/{appointment_id}/correction`

### Audited Correction Protocol:
1. The original step record and its historical payload are preserved in `procurement_process_steps`.
2. A permanent historical audit record is inserted into `process_step_corrections`:
   - `original_data`: Full snapshot of the pre-correction values.
   - `corrected_data`: New validated values.
   - `reason`: Mandatory text justification entered by the employee.
   - `corrected_by`: User ID and Name of the officer authorizing the correction.
   - `created_at`: Exact timestamp.
3. An entry is simultaneously committed to the tamper-evident `process_audit_logs` table.
4. If the correction alters a quality or weighment parameter, subsequent dependent values are recalculated deterministically without altering prior completion timestamps.
