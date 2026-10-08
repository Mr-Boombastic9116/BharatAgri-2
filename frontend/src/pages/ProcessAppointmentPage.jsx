import React, { useState, useEffect, useRef } from 'react';
import {
  getProcurementProcessState,
  submitProcurementProcessStep,
  applyProcurementStepCorrection,
  scanMangoQuality,
  uploadProcessEvidence,
  recordStorageFinalCheck
} from '../services/api';
import {
  CheckCircle2,
  Clock,
  Lock,
  ArrowLeft,
  Upload,
  Camera,
  AlertTriangle,
  FileCheck,
  ShieldAlert,
  Scale,
  Sparkles,
  Layers,
  ChevronRight,
  Info,
  RefreshCw,
  Eye,
  Check,
  X,
  Warehouse,
  Truck,
  UserCheck,
  Image as ImageIcon
} from 'lucide-react';

export default function ProcessAppointmentPage({ user, appointmentId, navigate }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [stateData, setStateData] = useState(null);

  // Multi-Employee Attribution state - database employee assignments
  const [stepEmployeeIds, setStepEmployeeIds] = useState({
    1: '',
    2: '',
    3: '',
    4: '',
    5: '',
    6: ''
  });

  // Step 1: Verification & Gate Intake
  const [step1Form, setStep1Form] = useState({
    transport_method: "Farmer's Own",
    truck_number: '',
    collected_bags: '',
    gross_weight_estimate: '',
    intake_notes: '',
    evidence_url: ''
  });
  const [step1EvidenceFile, setStep1EvidenceFile] = useState(null);
  const [step1EvidencePreview, setStep1EvidencePreview] = useState(null);
  const step1FileRef = useRef(null);

  // Step 2: Physical QC
  const [step2Form, setStep2Form] = useState({
    moisture_content_pct: '12.0',
    foreign_matter_pct: '1.0',
    broken_grains_pct: '0.0',
    damaged_grains_pct: '0.0',
    physical_observations: 'Produce dry, normal odor, clean grain surface',
    remarks: '',
    evidence_url: ''
  });
  const [step2EvidenceFile, setStep2EvidenceFile] = useState(null);
  const [step2EvidencePreview, setStep2EvidencePreview] = useState(null);
  const step2FileRef = useRef(null);

  // Step 3: AI QC (Mango)
  const [mangoImageFile, setMangoImageFile] = useState(null);
  const [mangoImagePreview, setMangoImagePreview] = useState(null);
  const [scanningMango, setScanningMango] = useState(false);
  const [mangoScanResult, setMangoScanResult] = useState(null);
  const [mangoScanError, setMangoScanError] = useState('');
  const [step3ReviewAction, setStep3ReviewAction] = useState('ACCEPT');
  const [step3ReviewNotes, setStep3ReviewNotes] = useState('');
  const fileInputRef = useRef(null);

  // Step 4: Weighment
  const [step4Form, setStep4Form] = useState({
    gross_weight_quintals: '',
    tare_weight_quintals: '2.5',
    weighbridge_id: 'WB-01',
    evidence_url: ''
  });
  const [step4EvidenceFile, setStep4EvidenceFile] = useState(null);
  const [step4EvidencePreview, setStep4EvidencePreview] = useState(null);
  const step4FileRef = useRef(null);

  // Step 5: Procurement
  const [step5Form, setStep5Form] = useState({
    warehouse_location: 'Warehouse Bay A-1',
    rate_per_quintal_inr: '',
    notes: '',
    evidence_url: ''
  });
  const [step5EvidenceFile, setStep5EvidenceFile] = useState(null);
  const [step5EvidencePreview, setStep5EvidencePreview] = useState(null);
  const step5FileRef = useRef(null);

  // Step 6: Storage Final Check
  const [storageForm, setStorageForm] = useState({
    storage_employee_name: 'Supervisor Prakash Rane',
    storage_employee_id: 'EMP-STR-06',
    received_quantity_quintals: '',
    storage_condition: 'Optimal Humidity & Temperature',
    physical_condition: 'Intact - No Infestation / Good Stacking',
    remarks: 'Produce transferred into storage stack Bay A-1. Physical integrity verified.',
    evidence_url: ''
  });
  const [storageEvidenceFile, setStorageEvidenceFile] = useState(null);
  const [storageEvidencePreview, setStorageEvidencePreview] = useState(null);
  const storageFileRef = useRef(null);
  const [submittingStorage, setSubmittingStorage] = useState(false);

  // Submitting step state
  const [submittingStep, setSubmittingStep] = useState(false);

  // Audited Correction Modal State
  const [showCorrectionModal, setShowCorrectionModal] = useState(false);
  const [correctionForm, setCorrectionForm] = useState({
    step_number: 1,
    field_name: 'truck_number',
    new_value: '',
    correction_reason: ''
  });
  const [submittingCorrection, setSubmittingCorrection] = useState(false);
  const [correctionMsg, setCorrectionMsg] = useState('');

  const loadState = async () => {
    if (!appointmentId) {
      setError('No appointment ID specified.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await getProcurementProcessState(appointmentId);
      if (res && res.success) {
        setStateData(res);
        if (res.mango_ai) {
          setMangoScanResult(res.mango_ai);
        }
        // Auto-fill defaults based on appointment
        if (res.appointment) {
          setStep1Form(prev => ({
            ...prev,
            gross_weight_estimate: String(res.appointment.booked_quantity || '')
          }));
          setStep4Form(prev => ({
            ...prev,
            gross_weight_quintals: String((res.appointment.booked_quantity || 25) + 2.5)
          }));
          setStorageForm(prev => ({
            ...prev,
            received_quantity_quintals: String(res.appointment.booked_quantity || 25)
          }));
        }
        if (res.pricing?.estimated_msp) {
          setStep5Form(prev => ({
            ...prev,
            rate_per_quintal_inr: String(res.pricing.estimated_msp)
          }));
        }
        if (res.available_employees && res.available_employees.length > 0) {
          const emps = res.available_employees;
          setStepEmployeeIds(prev => {
            const updated = { ...prev };
            const findByRole = (kw) => emps.find(e => e.role && e.role.toLowerCase().includes(kw.toLowerCase())) || emps[0];
            if (!updated[1]) updated[1] = String(findByRole('Intake').id);
            if (!updated[2]) updated[2] = String(findByRole('QC').id);
            if (!updated[3]) updated[3] = String(findByRole('AI').id);
            if (!updated[4]) updated[4] = String(findByRole('Weigh').id);
            if (!updated[5]) updated[5] = String(findByRole('Procurement').id);
            if (!updated[6]) updated[6] = String(findByRole('Storage').id);
            return updated;
          });
        }
      } else {
        setError('Could not retrieve appointment process state.');
      }
    } catch (err) {
      setError(err.message || 'Error loading process state.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadState();
  }, [appointmentId]);

  // Generic Evidence Upload Helper
  const handleUploadStepEvidence = async (file, stepNumber, evidenceType) => {
    if (!file) return null;
    const empList = stateData?.available_employees || [];
    const empObj = empList.find(e => String(e.id) === String(stepEmployeeIds[stepNumber])) || empList[0];
    const uploaderName = empObj?.name || user?.name || 'Staff';
    const fd = new FormData();
    fd.append('file', file);
    fd.append('process_step', `STEP_${stepNumber}`);
    fd.append('evidence_type', evidenceType);
    fd.append('notes', `Evidence photo for Step ${stepNumber} uploaded by ${uploaderName}`);
    const res = await uploadProcessEvidence(appointmentId, fd);
    return res?.evidence?.file_path || null;
  };

  // Handle Mango Image Selection
  const handleSelectMangoImage = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type.toLowerCase())) {
      setMangoScanError('Only JPG, PNG, and WEBP formats are supported.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setMangoScanError('File size must not exceed 10MB.');
      return;
    }
    setMangoScanError('');
    setMangoImageFile(file);
    const reader = new FileReader();
    reader.onload = () => setMangoImagePreview(reader.result);
    reader.readAsDataURL(file);
  };

  // Run Mango AI Quality Scan
  const handleRunMangoScan = async () => {
    if (!mangoImageFile) {
      setMangoScanError('Please select or capture a photograph containing sampled mangoes.');
      return;
    }
    setScanningMango(true);
    setMangoScanError('');
    try {
      const res = await scanMangoQuality(appointmentId, mangoImageFile);
      if (res && res.success) {
        setMangoScanResult(res);
        setSuccessMsg(`Mango AI scan completed! Successfully analyzed ${res.mangoes_detected} sampled fruit instance(s). Review complete optical analysis and final grade below.`);
      } else {
        setMangoScanError('Mango scan did not return a valid result.');
      }
    } catch (err) {
      setMangoScanError(err.message || 'Failed to complete Mango AI scan.');
    } finally {
      setScanningMango(false);
    }
  };

  // Submit Active Process Step
  const handleSubmitStep = async (stepNumber) => {
    setSubmittingStep(true);
    setError('');
    setSuccessMsg('');
    try {
      const empList = stateData?.available_employees || [];
      const chosenEmpId = stepEmployeeIds[stepNumber];
      const selectedEmp = empList.find(e => String(e.id) === String(chosenEmpId) || e.employee_code === chosenEmpId) || empList[0];

      if (!selectedEmp) {
        throw new Error('Please select an authorized employee from the centre staff database.');
      }

      let payload = {
        employee_name: selectedEmp.name,
        employee_id: selectedEmp.employee_code || String(selectedEmp.id)
      };

      if (stepNumber === 1) {
        let evUrl = step1Form.evidence_url;
        if (step1EvidenceFile && !evUrl) {
          evUrl = await handleUploadStepEvidence(step1EvidenceFile, 1, 'COLLECTION_PRODUCE');
        }
        payload = {
          ...payload,
          transport_method: step1Form.transport_method,
          truck_number: step1Form.transport_method === "Farmer's Own" ? '' : (step1Form.truck_number || 'PERSONAL_VEHICLE'),
          collected_bags: parseInt(step1Form.collected_bags || '0', 10),
          gross_weight_estimate: parseFloat(step1Form.gross_weight_estimate || '0'),
          intake_notes: step1Form.intake_notes,
          evidence_url: evUrl
        };
      } else if (stepNumber === 2) {
        let evUrl = step2Form.evidence_url;
        if (step2EvidenceFile && !evUrl) {
          evUrl = await handleUploadStepEvidence(step2EvidenceFile, 2, 'QUALITY_MACHINE');
        }
        payload = {
          ...payload,
          moisture_content_pct: parseFloat(step2Form.moisture_content_pct || '12.0'),
          foreign_matter_pct: parseFloat(step2Form.foreign_matter_pct || '1.0'),
          broken_grains_pct: parseFloat(step2Form.broken_grains_pct || '0.0'),
          damaged_grains_pct: parseFloat(step2Form.damaged_grains_pct || '0.0'),
          physical_observations: step2Form.physical_observations,
          remarks: step2Form.remarks,
          evidence_url: evUrl
        };
      } else if (stepNumber === 3) {
        const isMango = stateData?.appointment?.is_mango;
        if (isMango && !mangoScanResult) {
          throw new Error('Please upload and execute the Mango AI Quality Scan before completing Step 3.');
        }
        payload = {
          ...payload,
          review_action: step3ReviewAction,
          review_notes: step3ReviewNotes || 'Verified by Quality Inspection Officer'
        };
      } else if (stepNumber === 4) {
        const gross = parseFloat(step4Form.gross_weight_quintals || '0');
        const tare = parseFloat(step4Form.tare_weight_quintals || '0');
        if (gross <= tare) {
          throw new Error('Gross weight must be strictly greater than Tare weight.');
        }
        let evUrl = step4Form.evidence_url;
        if (step4EvidenceFile && !evUrl) {
          evUrl = await handleUploadStepEvidence(step4EvidenceFile, 4, 'WEIGHMENT');
        }
        payload = {
          ...payload,
          gross_weight_quintals: gross,
          tare_weight_quintals: tare,
          weighbridge_id: step4Form.weighbridge_id,
          evidence_url: evUrl
        };
      } else if (stepNumber === 5) {
        let evUrl = step5Form.evidence_url;
        if (step5EvidenceFile && !evUrl) {
          evUrl = await handleUploadStepEvidence(step5EvidenceFile, 5, 'QUALITY_INSPECTION');
        }
        const dbMspRate = stateData?.pricing?.estimated_msp || 2200;
        payload = {
          ...payload,
          warehouse_location: step5Form.warehouse_location,
          rate_per_quintal_inr: parseFloat(step5Form.rate_per_quintal_inr || dbMspRate),
          notes: step5Form.notes,
          evidence_url: evUrl
        };
      }

      const res = await submitProcurementProcessStep(appointmentId, stepNumber, payload);
      if (res && res.success) {
        setSuccessMsg(res.message || `Step ${stepNumber} completed successfully!`);
        await loadState();
      }
    } catch (err) {
      setError(err.message || `Failed to submit Step ${stepNumber}.`);
    } finally {
      setSubmittingStep(false);
    }
  };

  // Submit Independent Storage Final Check
  const handleStorageCheckSubmit = async () => {
    setSubmittingStorage(true);
    setError('');
    setSuccessMsg('');
    try {
      let evUrl = storageForm.evidence_url;
      if (storageEvidenceFile && !evUrl) {
        evUrl = await handleUploadStepEvidence(storageEvidenceFile, 6, 'STORAGE');
      }

      const payload = {
        storage_employee_name: storageForm.storage_employee_name || 'Supervisor Prakash Rane',
        storage_employee_id: storageForm.storage_employee_id || 'EMP-STR-06',
        received_quantity_quintals: parseFloat(storageForm.received_quantity_quintals || stateData?.appointment?.booked_quantity || 25),
        storage_condition: storageForm.storage_condition,
        physical_condition: storageForm.physical_condition,
        remarks: storageForm.remarks,
        evidence_url: evUrl
      };

      const res = await recordStorageFinalCheck(appointmentId, payload);
      if (res && res.success) {
        setSuccessMsg('Storage Final Check completed and audited successfully!');
        await loadState();
      }
    } catch (err) {
      setError(err.message || 'Failed to complete storage check.');
    } finally {
      setSubmittingStorage(false);
    }
  };

  // Submit Audited Correction
  const handleSubmitCorrection = async (e) => {
    e.preventDefault();
    setSubmittingCorrection(true);
    setCorrectionMsg('');
    setError('');
    try {
      const res = await applyProcurementStepCorrection(
        appointmentId,
        correctionForm.step_number,
        correctionForm.field_name,
        correctionForm.new_value,
        correctionForm.correction_reason
      );
      if (res && res.success) {
        setCorrectionMsg('Audited correction recorded successfully! Prior history preserved.');
        setSuccessMsg('Audited correction applied successfully.');
        setTimeout(() => {
          setShowCorrectionModal(false);
          setCorrectionMsg('');
          loadState();
        }, 1200);
      }
    } catch (err) {
      setError(err.message || 'Failed to apply audited correction.');
    } finally {
      setSubmittingCorrection(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <RefreshCw size={36} className="spin" color="var(--primary)" style={{ marginBottom: '16px' }} />
        <h3>Loading Procurement Workflow...</h3>
        <p style={{ color: 'var(--muted)' }}>Retrieving appointment records and verifying role access...</p>
      </div>
    );
  }

  const appt = stateData?.appointment;
  const steps = stateData?.steps || [];
  const currentStepNum = appt?.current_step_number || 1;
  const isCompletedAll = appt?.is_all_completed || false;
  const pricing = stateData?.pricing;
  const storageLot = stateData?.storage_lot;
  const evidenceList = stateData?.evidence || [];

  return (
    <div style={{ paddingBottom: '60px' }}>
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <button
          className="btn btn-outline"
          onClick={() => navigate('centre-dashboard')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <ArrowLeft size={16} /> Back to Centre Dashboard
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            className="btn btn-outline"
            onClick={() => setShowCorrectionModal(true)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', borderColor: '#f59e0b', color: '#b45309' }}
            title="Open audited correction form"
          >
            <ShieldAlert size={16} /> Request Audited Correction
          </button>
          <button
            className="btn btn-outline"
            onClick={loadState}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Global Alerts */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={20} />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <CheckCircle2 size={20} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Appointment Overview Header Card */}
      <div className="card shadow-sm" style={{ padding: '24px', borderRadius: '14px', marginBottom: '28px', background: 'var(--bg-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span className="badge badge-confirmed" style={{ fontSize: '0.8rem', fontWeight: 800 }}>
                {appt?.arrival_status || 'ARRIVED'}
              </span>
              <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                Lot Processing: {appt?.appointment_id}
              </h1>
            </div>
            <p style={{ margin: 0, color: 'var(--muted)', fontSize: '0.9rem' }}>
              Centre: <strong>{appt?.centre_name} ({appt?.state})</strong> | Farmer: <strong>{appt?.farmer_name}</strong> ({appt?.farmer_id})
            </p>
          </div>

          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Commodity</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)' }}>{appt?.crop}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Booked Quantity</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary)' }}>{appt?.booked_quantity} Quintals</div>
            </div>
            {pricing && (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>Estimated MSP</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#059669' }}>₹{pricing.estimated_msp} / q</div>
              </div>
            )}
          </div>
        </div>

        {/* Anti-Fraud Multi-Employee Isolation Callout */}
        <div style={{
          marginTop: '18px',
          padding: '12px 16px',
          background: 'rgba(59, 130, 246, 0.08)',
          borderRadius: '8px',
          borderLeft: '4px solid #3b82f6',
          fontSize: '0.85rem',
          color: '#1e40af',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <ShieldAlert size={18} color="#3b82f6" style={{ flexShrink: 0 }} />
          <span>
            <strong>Multi-Employee Separation & Data Isolation:</strong> Each step is independently executed by designated officers. Downstream workers cannot inspect sensitive upstream raw readings (moisture %, foreign matter %, tare/gross weights, rates) prior to independent recording.
          </span>
        </div>
      </div>

      {/* Sequential 5-Step Progress Tracker */}
      <div className="card shadow-sm" style={{ padding: '20px 24px', borderRadius: '14px', marginBottom: '28px', background: 'var(--bg-card)' }}>
        <h3 style={{ fontSize: '0.9rem', fontWeight: 800, textTransform: 'uppercase', color: 'var(--muted)', letterSpacing: '0.5px', marginBottom: '16px' }}>
          Sequential Procurement Process Sequence
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          {steps.map((st) => {
            const isCompleted = st.status === 'COMPLETED';
            const isCurrent = st.step_number === currentStepNum && !isCompletedAll;
            const isLocked = st.is_locked || (!isCompleted && !isCurrent);

            return (
              <div
                key={st.step_number}
                style={{
                  padding: '14px',
                  borderRadius: '10px',
                  border: isCurrent
                    ? '2px solid var(--primary)'
                    : isCompleted
                    ? '1px solid #10b981'
                    : '1px solid var(--border)',
                  background: isCurrent
                    ? 'rgba(16, 185, 129, 0.06)'
                    : isCompleted
                    ? 'rgba(16, 185, 129, 0.08)'
                    : 'var(--bg-page)',
                  opacity: isLocked ? 0.65 : 1.0,
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--muted)' }}>
                    STEP {st.step_number}
                  </span>
                  {isCompleted ? (
                    <span style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 800 }}>
                      <CheckCircle2 size={14} /> DONE
                    </span>
                  ) : isCurrent ? (
                    <span style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 800 }}>
                      <Clock size={14} /> ACTIVE
                    </span>
                  ) : (
                    <span style={{ color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 700 }}>
                      <Lock size={12} /> LOCKED
                    </span>
                  )}
                </div>

                <div style={{ fontWeight: 700, fontSize: '0.88rem', color: isCurrent ? 'var(--primary)' : 'var(--secondary)' }}>
                  {st.title}
                </div>

                {isCompleted && st.employee_name && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '4px' }}>
                    By: {st.employee_name}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ACTIVE STEP WORKFLOW FORM */}
      {!isCompletedAll ? (
        <div className="card shadow-sm" style={{ padding: '28px', borderRadius: '14px', background: 'var(--bg-card)', marginBottom: '28px' }}>
          {/* Employee Attribution Bar for Current Step */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(15, 23, 42, 0.03)',
            padding: '10px 16px',
            borderRadius: '8px',
            marginBottom: '20px',
            border: '1px solid var(--border)',
            flexWrap: 'wrap',
            gap: '10px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
              <UserCheck size={16} color="var(--primary)" />
              <span style={{ fontWeight: 700, color: 'var(--secondary)' }}>Assigned Employee for Step {currentStepNum}:</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <select
                className="form-control"
                style={{ padding: '6px 12px', fontSize: '0.85rem', minWidth: '320px', fontWeight: 600 }}
                value={stepEmployeeIds[currentStepNum] || ''}
                onChange={e => setStepEmployeeIds({ ...stepEmployeeIds, [currentStepNum]: e.target.value })}
              >
                {(stateData?.available_employees && stateData.available_employees.length > 0) ? (
                  stateData.available_employees.map(emp => (
                    <option key={emp.id} value={emp.id}>
                      {emp.name} ({emp.employee_code}) — {emp.role}
                    </option>
                  ))
                ) : (
                  <option value="">No employees found in centre database</option>
                )}
              </select>
            </div>
          </div>

          {/* STEP 1: VERIFICATION & COLLECTION INTAKE */}
          {currentStepNum === 1 && (
            <div>
              <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '14px', marginBottom: '20px' }}>
                <span className="badge badge-pending" style={{ marginBottom: '6px' }}>Step 1 of 5</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                  Initial Verification & Gate Collection Intake
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.875rem', margin: '4px 0 0 0' }}>
                  Verify farmer arrival, produce delivery method (not hardcoded to trucks), initial physical condition, and capture intake photo evidence.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div className="form-group">
                  <label className="form-label">Transport Method</label>
                  <select
                    className="form-control"
                    value={step1Form.transport_method}
                    onChange={e => setStep1Form({ ...step1Form, transport_method: e.target.value })}
                  >
                    <option value="Farmer's Own">Farmer's Own (Personal Arrival)</option>
                    <option value="Tractor">Tractor / Farm Trailer</option>
                    <option value="Private Vehicle">Private Vehicle / Auto / Mini-Van</option>
                    <option value="Hired Vehicle">Hired Vehicle</option>
                    <option value="Transporter">Commercial Transporter / Truck</option>
                    <option value="Other">Other Method</option>
                  </select>
                </div>

                {step1Form.transport_method !== "Farmer's Own" ? (
                  <div className="form-group">
                    <label className="form-label">Vehicle Registration Plate</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. GA-01-AB-1234 or MH-12-CD-5678"
                      value={step1Form.truck_number}
                      onChange={e => setStep1Form({ ...step1Form, truck_number: e.target.value })}
                    />
                  </div>
                ) : (
                  <div className="form-group">
                    <label className="form-label" style={{ color: 'var(--muted)' }}>Vehicle Plate (Optional)</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Personal produce arrival (No vehicle plate required)"
                      value={step1Form.truck_number}
                      onChange={e => setStep1Form({ ...step1Form, truck_number: e.target.value })}
                    />
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Number of Bardan Bags / Crates</label>
                  <input
                    type="number"
                    min="1"
                    className="form-control"
                    placeholder="e.g. 50"
                    value={step1Form.collected_bags}
                    onChange={e => setStep1Form({ ...step1Form, collected_bags: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Estimated Gross Quantity (Quintals)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    placeholder="e.g. 25.0"
                    value={step1Form.gross_weight_estimate}
                    onChange={e => setStep1Form({ ...step1Form, gross_weight_estimate: e.target.value })}
                  />
                </div>
              </div>

              {/* Photo Evidence Capture: Step 1 Produce Intake */}
              <div style={{
                background: 'var(--bg-page)',
                padding: '16px 20px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--secondary)' }}>
                      Step 1 Produce Intake Photo Evidence
                    </h4>
                    <p style={{ margin: '2px 0 0 0', color: 'var(--muted)', fontSize: '0.78rem' }}>
                      Capture or upload photograph showing actual produce received from the farmer at the collection dock.
                    </p>
                  </div>
                  <input
                    type="file"
                    ref={step1FileRef}
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setStep1EvidenceFile(file);
                        const r = new FileReader();
                        r.onload = () => setStep1EvidencePreview(r.result);
                        r.readAsDataURL(file);
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => step1FileRef.current?.click()}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                  >
                    <Camera size={14} /> Capture / Select Photo
                  </button>
                </div>

                {step1EvidencePreview && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '10px' }}>
                    <img
                      src={step1EvidencePreview}
                      alt="Produce intake evidence"
                      style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border)' }}
                    />
                    <div style={{ fontSize: '0.82rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} /> Produce intake photo attached ({step1EvidenceFile?.name})
                    </div>
                  </div>
                )}
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="form-label">Gate Intake Notes / Observation</label>
                <textarea
                  className="form-control"
                  rows="2"
                  placeholder="Record dock condition, initial visual quality, packaging integrity..."
                  value={step1Form.intake_notes}
                  onChange={e => setStep1Form({ ...step1Form, intake_notes: e.target.value })}
                />
              </div>

              <button
                className="btn btn-primary"
                onClick={() => handleSubmitStep(1)}
                disabled={submittingStep}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px' }}
              >
                {submittingStep ? <RefreshCw size={16} className="spin" /> : <Check size={16} />}
                Complete Step 1 & Advance to Physical QC
              </button>
            </div>
          )}

          {/* STEP 2: PHYSICAL QUALITY INSPECTION */}
          {currentStepNum === 2 && (
            <div>
              <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '14px', marginBottom: '20px' }}>
                <span className="badge badge-pending" style={{ marginBottom: '6px' }}>Step 2 of 5</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                  Physical Quality Inspection (Manual Instrument QC)
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.875rem', margin: '4px 0 0 0' }}>
                  Independent quality officer measures moisture content and inerts using calibrated testing equipment.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div className="form-group">
                  <label className="form-label">
                    Moisture Meter Content (% w/w) <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="40"
                    className="form-control"
                    value={step2Form.moisture_content_pct}
                    onChange={e => setStep2Form({ ...step2Form, moisture_content_pct: e.target.value })}
                    required
                  />
                  <small style={{ color: 'var(--muted)' }}>Standard permissible tolerance: ≤ 14.0%</small>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Foreign Matter / Inerts (%) <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="20"
                    className="form-control"
                    value={step2Form.foreign_matter_pct}
                    onChange={e => setStep2Form({ ...step2Form, foreign_matter_pct: e.target.value })}
                    required
                  />
                  <small style={{ color: 'var(--muted)' }}>Dust, chaff, stones, or stalk matter</small>
                </div>

                <div className="form-group">
                  <label className="form-label">Broken / Immature Produce (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    className="form-control"
                    value={step2Form.broken_grains_pct}
                    onChange={e => setStep2Form({ ...step2Form, broken_grains_pct: e.target.value })}
                  />
                </div>
              </div>

              {/* Photo Evidence Capture: Step 2 Moisture Meter Equipment */}
              <div style={{
                background: 'var(--bg-page)',
                padding: '16px 20px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--secondary)' }}>
                      Step 2 Testing Machine / Moisture Meter Photo Evidence
                    </h4>
                    <p style={{ margin: '2px 0 0 0', color: 'var(--muted)', fontSize: '0.78rem' }}>
                      Capture photograph of the moisture testing meter screen or physical testing apparatus.
                    </p>
                  </div>
                  <input
                    type="file"
                    ref={step2FileRef}
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setStep2EvidenceFile(file);
                        const r = new FileReader();
                        r.onload = () => setStep2EvidencePreview(r.result);
                        r.readAsDataURL(file);
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => step2FileRef.current?.click()}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                  >
                    <Camera size={14} /> Capture / Upload Machine Photo
                  </button>
                </div>

                {step2EvidencePreview && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '10px' }}>
                    <img
                      src={step2EvidencePreview}
                      alt="QC machine evidence"
                      style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border)' }}
                    />
                    <div style={{ fontSize: '0.82rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} /> Moisture meter reading photo attached ({step2EvidenceFile?.name})
                    </div>
                  </div>
                )}
              </div>

              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label className="form-label">Physical Inspection Checklist & Observations</label>
                <input
                  type="text"
                  className="form-control"
                  value={step2Form.physical_observations}
                  onChange={e => setStep2Form({ ...step2Form, physical_observations: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="form-label">QC Inspector Remarks</label>
                <textarea
                  className="form-control"
                  rows="2"
                  placeholder="Record instrument calibration ID, sampling method..."
                  value={step2Form.remarks}
                  onChange={e => setStep2Form({ ...step2Form, remarks: e.target.value })}
                />
              </div>

              <button
                className="btn btn-primary"
                onClick={() => handleSubmitStep(2)}
                disabled={submittingStep}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px' }}
              >
                {submittingStep ? <RefreshCw size={16} className="spin" /> : <Check size={16} />}
                Complete Step 2 & Advance to AI Visual Scan
              </button>
            </div>
          )}

          {/* STEP 3: AI VISUAL QUALITY INSPECTION */}
          {currentStepNum === 3 && (
            <div>
              <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '14px', marginBottom: '20px' }}>
                <span className="badge badge-pending" style={{ marginBottom: '6px' }}>Step 3 of 5</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                  Visual Quality Inspection {appt?.is_mango ? '(Mango AI Quality & Ripeness Scan)' : ''}
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.875rem', margin: '4px 0 0 0' }}>
                  {appt?.is_mango
                    ? 'Sample multiple representative mangoes into ONE photograph. Watershed distance-transform isolates touching mangoes, classifying defects and estimating visual ripeness stages.'
                    : `Current crop is ${appt?.crop}. AI image scanning is currently available for MANGO ONLY.`}
                </p>
              </div>

              {!appt?.is_mango ? (
                <div>
                  <div style={{
                    padding: '20px',
                    borderRadius: '12px',
                    background: 'var(--bg-page)',
                    border: '1px solid var(--border)',
                    marginBottom: '24px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px'
                  }}>
                    <Info size={28} color="var(--primary)" />
                    <div>
                      <h4 style={{ margin: 0, fontWeight: 700, color: 'var(--secondary)' }}>
                        Mango AI Scanner Not Applicable for {appt?.crop}
                      </h4>
                      <p style={{ margin: '4px 0 0 0', color: 'var(--muted)', fontSize: '0.875rem' }}>
                        The prototype AI visual quality inspection model currently supports <strong>MANGO ONLY</strong>.
                        Visual inspection for {appt?.crop} proceeds under standard physical verification protocols.
                      </p>
                    </div>
                  </div>

                  <div className="form-group" style={{ marginBottom: '24px' }}>
                    <label className="form-label">Visual Inspection Notes</label>
                    <textarea
                      className="form-control"
                      rows="2"
                      value={step3ReviewNotes}
                      placeholder="Standard visual appearance normal, color uniform, free of pest contamination."
                      onChange={e => setStep3ReviewNotes(e.target.value)}
                    />
                  </div>

                  <button
                    className="btn btn-primary"
                    onClick={() => handleSubmitStep(3)}
                    disabled={submittingStep}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px' }}
                  >
                    {submittingStep ? <RefreshCw size={16} className="spin" /> : <Check size={16} />}
                    Confirm Visual Inspection & Advance to Weighment
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{
                    border: '2px dashed var(--border)',
                    borderRadius: '14px',
                    padding: '30px',
                    textAlign: 'center',
                    background: 'var(--bg-page)',
                    marginBottom: '24px'
                  }}>
                    <input
                      type="file"
                      ref={fileInputRef}
                      style={{ display: 'none' }}
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleSelectMangoImage}
                    />

                    {!mangoImagePreview ? (
                      <div>
                        <Sparkles size={40} color="var(--primary)" style={{ marginBottom: '12px' }} />
                        <h4 style={{ fontWeight: 800, color: 'var(--secondary)', marginBottom: '6px' }}>
                          Upload Multi-Mango Representative Sample Photo
                        </h4>
                        <p style={{ color: 'var(--muted)', fontSize: '0.875rem', maxWidth: '520px', margin: '0 auto 18px auto' }}>
                          Place representative sampled mangoes together on a surface. Take <strong>ONE photo containing multiple mangoes</strong>. Watershed segmentation partitions touching fruits.
                        </p>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                          <button
                            type="button"
                            className="btn btn-primary"
                            onClick={() => fileInputRef.current?.click()}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                          >
                            <Upload size={16} /> Choose Image
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => fileInputRef.current?.click()}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                          >
                            <Camera size={16} /> Camera Capture
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ maxWidth: '480px', margin: '0 auto 18px auto', borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border)' }}>
                          <img
                            src={mangoImagePreview}
                            alt="Sampled Mangoes Preview"
                            style={{ width: '100%', maxHeight: '320px', objectFit: 'contain', display: 'block', background: '#000' }}
                          />
                        </div>
                        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                          <button
                            type="button"
                            className="btn btn-primary"
                            onClick={handleRunMangoScan}
                            disabled={scanningMango}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                          >
                            {scanningMango ? <RefreshCw size={16} className="spin" /> : <Sparkles size={16} />}
                            {scanningMango ? 'Partitioning Touching Mangoes & Scanning...' : 'Execute Mango AI Quality Scan'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-outline"
                            onClick={() => {
                              setMangoImageFile(null);
                              setMangoImagePreview(null);
                              setMangoScanResult(null);
                            }}
                            disabled={scanningMango}
                          >
                            Reset
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {mangoScanError && (
                    <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
                      {mangoScanError}
                    </div>
                  )}

                  {/* AI Scan Results Display */}
                  {mangoScanResult && (
                    <div style={{
                      background: 'var(--bg-page)',
                      borderRadius: '12px',
                      padding: '24px',
                      border: '1px solid var(--border)',
                      marginBottom: '24px'
                    }}>
                      {/* Analysis Header - No Grade Badge Here */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', flexWrap: 'wrap', gap: '10px' }}>
                        <div>
                          <h3 style={{ margin: 0, fontWeight: 800, color: 'var(--secondary)' }}>
                            Mango AI Optical Surface & Defect Analysis
                          </h3>
                          <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Instance-level boundary segmentation, defect lesion isolation & transparent grading ({mangoScanResult.model_version || 'mango-quality-v1'})
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Model Architecture</span>
                          <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>{mangoScanResult.model_type}</div>
                        </div>
                      </div>

                      {/* 1. Annotated Image View */}
                      {mangoScanResult.annotated_image_url && (
                        <div style={{ marginBottom: '20px', borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--border)' }}>
                          <div style={{ padding: '8px 12px', background: 'var(--surface-secondary)', borderBottom: '1px solid var(--border)', fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-secondary)' }}>
                            Annotated Multi-Fruit Scan & Boundary Detection
                          </div>
                          <img
                            src={mangoScanResult.annotated_image_url}
                            alt="Annotated Mango Scan"
                            style={{ width: '100%', maxHeight: '420px', objectFit: 'contain', display: 'block', background: '#0f172a' }}
                          />
                        </div>
                      )}

                      {/* 2. Visual Debug Mode: All 10 Stages */}
                      {mangoScanResult.debug_images && Object.keys(mangoScanResult.debug_images).length > 0 && (
                        <div style={{ marginBottom: '20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '10px', padding: '14px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                            <h4 style={{ margin: 0, fontSize: '0.88rem', fontWeight: 800, color: 'var(--secondary)' }}>
                              🔬 Developer & Inspection Pipeline Visual Debug Stages (10 Stages)
                            </h4>
                            <span style={{ fontSize: '0.72rem', background: 'var(--primary)', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                              Verified Boundary Evidence
                            </span>
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                            {Object.entries(mangoScanResult.debug_images).filter(([k]) => k !== 'debug_2_peel_mask').map(([k, url]) => {
                              const stageLabels = {
                                debug_1_original: "Stage 1: Original Image",
                                debug_2_bunch_bbox: "Stage 2: Bunch Peel & BBox",
                                debug_3_separation_boundaries: "Stage 3: Boundary Creases & Seams",
                                debug_4_instance_masks: "Stage 4: Instance Masks",
                                debug_5_crops_montage: "Stage 5: Separated Crops",
                                debug_6_background_excluded: "Stage 6: Background Excluded Region",
                                debug_7_defect_candidates: "Stage 7: Defect Candidate Lesions",
                                debug_8_final_defect_mask: "Stage 8: Final Defect Mask (Safe Interior)",
                                debug_9_defect_percentage: "Stage 9: Defect Percentage Overlay",
                                debug_10_final_grade: "Stage 10: Final Quality Grade Card"
                              };
                              return (
                                <div key={k} style={{ textAlign: 'center', background: '#0f172a', borderRadius: '8px', padding: '8px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
                                  <div style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 700, marginBottom: '6px' }}>
                                    {stageLabels[k] || k}
                                  </div>
                                  <img src={url} alt={k} style={{ width: '100%', maxHeight: '130px', objectFit: 'contain', borderRadius: '4px' }} />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 3. Detection Information & Summary Metrics */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px', marginBottom: '20px' }}>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center' }}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700 }}>Total Detected</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--secondary)' }}>
                            {mangoScanResult.mangoes_detected !== undefined ? mangoScanResult.mangoes_detected : (mangoScanResult.sample_count || (mangoScanResult.detections ? mangoScanResult.detections.length : 0))}
                          </div>
                        </div>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center', borderLeft: '3px solid #10b981' }}>
                          <div style={{ fontSize: '0.75rem', color: '#047857', fontWeight: 700 }}>Healthy</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#047857' }}>
                            {mangoScanResult.healthy !== undefined ? mangoScanResult.healthy : (mangoScanResult.healthy_count !== undefined ? mangoScanResult.healthy_count : (mangoScanResult.detections ? mangoScanResult.detections.filter(d => d.health_status === 'Healthy').length : 0))}
                          </div>
                        </div>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center', borderLeft: '3px solid #ef4444' }}>
                          <div style={{ fontSize: '0.75rem', color: '#b91c1c', fontWeight: 700 }}>Defective</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#b91c1c' }}>
                            {mangoScanResult.defect_count !== undefined ? mangoScanResult.defect_count : (mangoScanResult.detections ? mangoScanResult.detections.filter(d => d.health_status === 'Defective').length : 0)}
                          </div>
                        </div>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center', borderLeft: '3px solid #eab308' }}>
                          <div style={{ fontSize: '0.75rem', color: '#a16207', fontWeight: 700 }}>Ripe</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#a16207' }}>{mangoScanResult.ripe_count || 0}</div>
                        </div>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center', borderLeft: '3px solid #84cc16' }}>
                          <div style={{ fontSize: '0.75rem', color: '#4d7c0f', fontWeight: 700 }}>Nearly Ripe</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#4d7c0f' }}>{mangoScanResult.nearly_ripe_count || 0}</div>
                        </div>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center', borderLeft: '3px solid #065f46' }}>
                          <div style={{ fontSize: '0.75rem', color: '#065f46', fontWeight: 700 }}>Not Ripe</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#065f46' }}>{mangoScanResult.not_ripe_count || 0}</div>
                        </div>
                        <div className="stat-card" style={{ padding: '12px', textAlign: 'center', borderLeft: '3px solid #9ca3af' }}>
                          <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700 }}>Avg Defect %</div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text)' }}>{mangoScanResult.affected_percentage || 0}%</div>
                        </div>
                      </div>

                      {/* 4. Individual Mango Instances Grid with Size, Color & Defect Info */}
                      {mangoScanResult.detections && mangoScanResult.detections.length > 0 && (
                        <div style={{ marginBottom: '24px' }}>
                          <h4 style={{ fontSize: '0.92rem', fontWeight: 800, marginBottom: '10px', color: 'var(--secondary)' }}>
                            Individual Segmented Mango Detections ({mangoScanResult.detections.length} Fruit Instances)
                          </h4>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                            {mangoScanResult.detections.map((d, i) => {
                              const isHealthy = (d.health_status === 'Healthy' || (!d.health_status && d.predicted_class === 'Healthy'));
                              const isDefective = (d.health_status === 'Defective' || (!d.health_status && d.predicted_class && d.predicted_class !== 'Healthy'));
                              const statusColor = isHealthy ? '#059669' : isDefective ? '#dc2626' : '#d97706';
                              const statusBg = isHealthy ? 'var(--success-bg)' : isDefective ? 'var(--danger-bg)' : 'var(--warning-bg)';
                              const statusLabel = d.health_status || (isHealthy ? 'Healthy' : 'Defective');

                              return (
                                <div
                                  key={i}
                                  style={{
                                    background: 'var(--surface)',
                                    border: `1.5px solid ${isHealthy ? 'var(--success)' : isDefective ? 'var(--danger)' : 'var(--border)'}`,
                                    borderRadius: '10px',
                                    padding: '12px',
                                    display: 'flex',
                                    gap: '12px',
                                    alignItems: 'flex-start'
                                  }}
                                >
                                  {d.crop_url && (
                                    <img
                                      src={d.crop_url}
                                      alt={`Mango #${d.sample_index}`}
                                      style={{ width: '74px', height: '74px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--border)' }}
                                    />
                                  )}
                                  <div style={{ flex: 1, fontSize: '0.8rem' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                      <strong style={{ color: 'var(--secondary)', fontSize: '0.88rem' }}>Mango #{d.sample_index}</strong>
                                      <span style={{
                                        fontSize: '0.72rem',
                                        fontWeight: 800,
                                        padding: '2px 8px',
                                        borderRadius: '4px',
                                        background: statusBg,
                                        color: statusColor
                                      }}>
                                        {statusLabel}
                                      </span>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.75rem', marginTop: '2px' }}>
                                      <div>Ripeness: <strong>{d.ripeness || 'Uncertain'}</strong></div>
                                      <div>Quality: <strong>{d.quality_grade || (isHealthy ? 'Grade A' : 'Reject')}</strong></div>
                                      <div>Defect: <strong style={{ color: isDefective ? 'var(--danger)' : 'var(--success)' }}>{d.defect_type || (isHealthy ? 'None' : d.predicted_class)}</strong></div>
                                      <div>Confidence: <strong>{d.confidence}%</strong></div>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.72rem', color: 'var(--muted)', marginTop: '4px' }}>
                                      <div>Visible Defect: <strong style={{ color: isDefective ? 'var(--danger)' : 'var(--text)' }}>{d.visible_defect_pct !== undefined ? d.visible_defect_pct : d.affected_area_pct}%</strong></div>
                                      <div>Est. 3D Severity: <strong>{d.estimated_total_surface_severity?.range_str || `${d.affected_area_pct}%`}</strong></div>
                                    </div>
                                    {d.grading_factors && (
                                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.70rem', color: 'var(--muted)', marginTop: '2px' }}>
                                        <div>Peel Uniformity: <strong>{d.grading_factors.colour_uniformity_score}/100</strong></div>
                                        <div>Shape Aspect: <strong>{d.grading_factors.shape_aspect_ratio} ({d.grading_factors.visibility})</strong></div>
                                      </div>
                                    )}
                                    {d.visual_evidence && (
                                      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '5px', fontStyle: 'italic', background: 'var(--surface-secondary)', padding: '4px 6px', borderRadius: '4px' }}>
                                        {d.visual_evidence}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 5. Lot-Level Aggregated Metrics & Analysis Status */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '24px', background: 'var(--surface-secondary)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                        <div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 700 }}>Inspection Reference</div>
                          <div style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--text)' }}>{mangoScanResult.inspection_code}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 700 }}>AI Analysis Confidence</div>
                          <div style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--text)' }}>{mangoScanResult.confidence}% (Model Baseline)</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.72rem', color: 'var(--muted)', textTransform: 'uppercase', fontWeight: 700 }}>Analysis Status</div>
                          <div style={{ fontWeight: 800, fontSize: '0.9rem', color: mangoScanResult.status === 'COMPLETED' ? 'var(--success)' : 'var(--warning)' }}>
                            {mangoScanResult.status}
                          </div>
                        </div>
                      </div>

                      {/* Divider Leading to Final Grade */}
                      <div style={{ borderTop: '2px dashed var(--border)', margin: '24px 0 20px 0' }} />

                      {/* 6. PROMINENT FINAL GRADE SECTION */}
                      <div style={{
                        background: 'var(--surface-elevated)',
                        borderRadius: '12px',
                        padding: '20px',
                        border: '2px solid var(--border)',
                        boxShadow: 'var(--shadow-md)',
                        marginBottom: '16px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '14px' }}>
                          <div>
                            <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--muted)' }}>
                              Final Inspection Conclusion
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '4px' }}>
                              <span style={{
                                fontSize: '1.6rem',
                                fontWeight: 900,
                                padding: '4px 16px',
                                borderRadius: '8px',
                                background: mangoScanResult.visual_grade === 'Grade A' ? 'var(--success-bg)' : mangoScanResult.visual_grade === 'Grade B' ? 'var(--warning-bg)' : 'var(--danger-bg)',
                                color: mangoScanResult.visual_grade === 'Grade A' ? 'var(--success)' : mangoScanResult.visual_grade === 'Grade B' ? 'var(--warning)' : 'var(--danger)',
                                border: `1.5px solid ${mangoScanResult.visual_grade === 'Grade A' ? 'var(--success)' : mangoScanResult.visual_grade === 'Grade B' ? 'var(--warning)' : 'var(--danger)'}`
                              }}>
                                {mangoScanResult.visual_grade || 'Grade A'}
                              </span>
                              <div>
                                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--secondary)' }}>
                                  {mangoScanResult.lot_quality_grade || 'Standard Quality'}
                                </div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                                  Estimated Defect Rate: {mangoScanResult.affected_percentage || 0}% across {mangoScanResult.sample_count || mangoScanResult.mangoes_detected || 1} instance(s)
                                </div>
                              </div>
                            </div>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>Maturity Dominance</div>
                            <div style={{ fontWeight: 800, fontSize: '0.9rem', color: 'var(--text)' }}>
                              {mangoScanResult.ripeness_summary ? Object.entries(mangoScanResult.ripeness_summary).sort((a,b)=>b[1]-a[1])[0]?.[0] : 'Ripe'}
                            </div>
                          </div>
                        </div>

                        {/* Summary Rationale */}
                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', background: 'var(--surface-secondary)', padding: '10px 14px', borderRadius: '8px', marginBottom: '14px', lineHeight: 1.5 }}>
                          {mangoScanResult.lot_grading_summary || `Lot optical evaluation concludes ${mangoScanResult.visual_grade} based on surface defect analysis and instance segmentation.`}
                        </div>

                        <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginBottom: '16px', fontStyle: 'italic' }}>
                          {mangoScanResult.grading_disclaimer || "AI-estimated potential grade based on multi-factor optical analysis; transparent baseline for decision support, not an official statutory APMC certification."}
                        </div>

                        {/* Human Review / Override Decision Form */}
                        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '14px' }}>
                          <h4 style={{ fontSize: '0.88rem', fontWeight: 800, marginBottom: '10px', color: 'var(--secondary)' }}>
                            Inspector Quality Certification Decision
                          </h4>

                          <div style={{ display: 'flex', gap: '16px', marginBottom: '12px', flexWrap: 'wrap' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontWeight: 600 }}>
                              <input
                                type="radio"
                                name="reviewAction"
                                value="ACCEPT"
                                checked={step3ReviewAction === 'ACCEPT'}
                                onChange={() => setStep3ReviewAction('ACCEPT')}
                              />
                              Accept AI Grade ({mangoScanResult.visual_grade})
                            </label>

                            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontWeight: 600, color: 'var(--warning)' }}>
                              <input
                                type="radio"
                                name="reviewAction"
                                value="OVERRIDE"
                                checked={step3ReviewAction === 'OVERRIDE'}
                                onChange={() => setStep3ReviewAction('OVERRIDE')}
                              />
                              Request Manual Override / Review
                            </label>
                          </div>

                          {step3ReviewAction === 'OVERRIDE' && (
                            <div className="form-group" style={{ marginBottom: '12px' }}>
                              <label className="form-label">Mandatory Override Reason</label>
                              <input
                                type="text"
                                className="form-control"
                                placeholder="e.g. Visual inspection confirms superficial sap stain rather than deep anthracnose necrosis"
                                value={step3ReviewNotes}
                                onChange={e => setStep3ReviewNotes(e.target.value)}
                                required
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  <button
                    className="btn btn-primary"
                    onClick={() => handleSubmitStep(3)}
                    disabled={submittingStep || !mangoScanResult}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px' }}
                  >
                    {submittingStep ? <RefreshCw size={16} className="spin" /> : <Check size={16} />}
                    Complete Step 3 & Advance to Weighment
                  </button>
                </div>
              )}
            </div>
          )}

          {/* STEP 4: WEIGHMENT */}
          {currentStepNum === 4 && (
            <div>
              <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '14px', marginBottom: '20px' }}>
                <span className="badge badge-pending" style={{ marginBottom: '6px' }}>Step 4 of 5</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                  Weighment & Gross/Tare Assessment
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.875rem', margin: '4px 0 0 0' }}>
                  Scale operator independently records gross weight on weighbridge and calculates net weight. Scale reading photo required for audit integrity.
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div className="form-group">
                  <label className="form-label">Gross Weight (Quintals) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="1"
                    className="form-control"
                    value={step4Form.gross_weight_quintals}
                    onChange={e => setStep4Form({ ...step4Form, gross_weight_quintals: e.target.value })}
                    required
                  />
                  <small style={{ color: 'var(--muted)' }}>Scale measurement including carrier and crates</small>
                </div>

                <div className="form-group">
                  <label className="form-label">Tare Weight (Quintals) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    className="form-control"
                    value={step4Form.tare_weight_quintals}
                    onChange={e => setStep4Form({ ...step4Form, tare_weight_quintals: e.target.value })}
                    required
                  />
                  <small style={{ color: 'var(--muted)' }}>Empty carrier/crates tare weight</small>
                </div>

                <div className="form-group">
                  <label className="form-label">Weighbridge Station ID</label>
                  <select
                    className="form-control"
                    value={step4Form.weighbridge_id}
                    onChange={e => setStep4Form({ ...step4Form, weighbridge_id: e.target.value })}
                  >
                    <option value="WB-01">Weighbridge WB-01 (Main Yard)</option>
                    <option value="WB-02">Weighbridge WB-02 (Heavy Truck Scale)</option>
                    <option value="WB-03">Weighbridge WB-03 (Precision Gate)</option>
                  </select>
                </div>
              </div>

              {/* Calculated Net Weight Card */}
              {parseFloat(step4Form.gross_weight_quintals || '0') > parseFloat(step4Form.tare_weight_quintals || '0') && (
                <div style={{
                  padding: '16px 20px',
                  background: 'rgba(16, 185, 129, 0.08)',
                  borderRadius: '10px',
                  border: '1px solid #10b981',
                  marginBottom: '20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#047857', textTransform: 'uppercase' }}>Computed Net Weight</span>
                    <h3 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 800, color: '#065f46' }}>
                      {(parseFloat(step4Form.gross_weight_quintals) - parseFloat(step4Form.tare_weight_quintals)).toFixed(2)} Quintals
                    </h3>
                  </div>
                  <Scale size={32} color="#10b981" />
                </div>
              )}

              {/* Photo Evidence Capture: Step 4 Weighbridge Display */}
              <div style={{
                background: 'var(--bg-page)',
                padding: '16px 20px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--secondary)' }}>
                      Step 4 Weighing Machine Display Photo Evidence
                    </h4>
                    <p style={{ margin: '2px 0 0 0', color: 'var(--muted)', fontSize: '0.78rem' }}>
                      Capture photograph of the weighing machine digital scale reading or weighbridge ticket.
                    </p>
                  </div>
                  <input
                    type="file"
                    ref={step4FileRef}
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setStep4EvidenceFile(file);
                        const r = new FileReader();
                        r.onload = () => setStep4EvidencePreview(r.result);
                        r.readAsDataURL(file);
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => step4FileRef.current?.click()}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                  >
                    <Camera size={14} /> Capture / Upload Scale Photo
                  </button>
                </div>

                {step4EvidencePreview && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '10px' }}>
                    <img
                      src={step4EvidencePreview}
                      alt="Weighbridge evidence"
                      style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border)' }}
                    />
                    <div style={{ fontSize: '0.82rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} /> Weighbridge scale photo attached ({step4EvidenceFile?.name})
                    </div>
                  </div>
                )}
              </div>

              <button
                className="btn btn-primary"
                onClick={() => handleSubmitStep(4)}
                disabled={submittingStep}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px' }}
              >
                {submittingStep ? <RefreshCw size={16} className="spin" /> : <Check size={16} />}
                Complete Step 4 & Advance to Procurement Finalization
              </button>
            </div>
          )}

          {/* STEP 5: PROCUREMENT & SETTLEMENT FINALIZATION */}
          {currentStepNum === 5 && (
            <div>
              <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '14px', marginBottom: '20px' }}>
                <span className="badge badge-pending" style={{ marginBottom: '6px' }}>Step 5 of 5</span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                  Procurement & Settlement Finalization
                </h2>
                <p style={{ color: 'var(--muted)', fontSize: '0.875rem', margin: '4px 0 0 0' }}>
                  Combine physical QC and AI visual assessment into the final grade, verify authentic database MSP, assign warehouse bay, and initiate Direct Benefit Transfer (DBT).
                </p>
              </div>

              {/* Authentic Database MSP Information Card */}
              {pricing && (
                <div style={{
                  padding: '16px 20px',
                  background: 'rgba(5, 150, 105, 0.08)',
                  borderRadius: '10px',
                  border: '1px solid #10b981',
                  marginBottom: '20px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#047857', textTransform: 'uppercase' }}>
                        Official Database MSP Benchmark ({pricing.state} | {pricing.season})
                      </span>
                      <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#065f46', marginTop: '2px' }}>
                        Estimated MSP: ₹{pricing.estimated_msp} / quintal
                      </div>
                      <div style={{ fontSize: '0.85rem', color: '#047857' }}>
                        Official MSP: ₹{pricing.official_msp} / quintal | Procurement Price: ₹{step5Form.rate_per_quintal_inr || pricing.estimated_msp} / quintal
                      </div>
                    </div>
                    <FileCheck size={36} color="#059669" />
                  </div>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div className="form-group">
                  <label className="form-label">Warehouse Storage Bay / Stack</label>
                  <input
                    type="text"
                    className="form-control"
                    value={step5Form.warehouse_location}
                    onChange={e => setStep5Form({ ...step5Form, warehouse_location: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Procurement Rate per Quintal (INR)</label>
                  <input
                    type="number"
                    step="1"
                    className="form-control"
                    value={step5Form.rate_per_quintal_inr}
                    onChange={e => setStep5Form({ ...step5Form, rate_per_quintal_inr: e.target.value })}
                  />
                  <small style={{ color: 'var(--muted)' }}>Directly uses estimated MSP from database: ₹{pricing?.estimated_msp || '2200'} / q</small>
                </div>
              </div>

              {/* Photo Evidence Capture: Step 5 Final Clearance */}
              <div style={{
                background: 'var(--bg-page)',
                padding: '16px 20px',
                borderRadius: '10px',
                border: '1px solid var(--border)',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <div>
                    <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: 'var(--secondary)' }}>
                      Step 5 Final Procurement Clearance Photo Evidence
                    </h4>
                    <p style={{ margin: '2px 0 0 0', color: 'var(--muted)', fontSize: '0.78rem' }}>
                      Attach photograph of procurement clearance docket or final quality acceptance.
                    </p>
                  </div>
                  <input
                    type="file"
                    ref={step5FileRef}
                    style={{ display: 'none' }}
                    accept="image/*"
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setStep5EvidenceFile(file);
                        const r = new FileReader();
                        r.onload = () => setStep5EvidencePreview(r.result);
                        r.readAsDataURL(file);
                      }
                    }}
                  />
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => step5FileRef.current?.click()}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                  >
                    <Camera size={14} /> Capture / Upload Clearance Photo
                  </button>
                </div>

                {step5EvidencePreview && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginTop: '10px' }}>
                    <img
                      src={step5EvidencePreview}
                      alt="Clearance evidence"
                      style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '6px', border: '1px solid var(--border)' }}
                    />
                    <div style={{ fontSize: '0.82rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle2 size={16} /> Clearance docket photo attached ({step5EvidenceFile?.name})
                    </div>
                  </div>
                )}
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="form-label">Procurement Officer Final Notes</label>
                <textarea
                  className="form-control"
                  rows="2"
                  placeholder="Record final dispatch condition, inspection clearance, farmer satisfaction..."
                  value={step5Form.notes}
                  onChange={e => setStep5Form({ ...step5Form, notes: e.target.value })}
                />
              </div>

              <button
                className="btn btn-primary"
                onClick={() => handleSubmitStep(5)}
                disabled={submittingStep}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px' }}
              >
                {submittingStep ? <RefreshCw size={16} className="spin" /> : <FileCheck size={16} />}
                Finalize Procurement & Authorize DBT Payment
              </button>
            </div>
          )}
        </div>
      ) : (
        /* ALL 5 STEPS COMPLETED SUMMARY */
        <div>
          {/* Procurement Success Banner */}
          <div className="card shadow-sm" style={{ padding: '36px 30px', borderRadius: '14px', textAlign: 'center', background: 'var(--bg-card)', marginBottom: '28px', border: '1px solid #10b981' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#10b981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <CheckCircle2 size={36} />
            </div>
            <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '8px' }}>
              Lot Procurement Successfully Finalized!
            </h2>
            <p style={{ color: 'var(--muted)', maxWidth: '560px', margin: '0 auto 20px auto', fontSize: '0.92rem', lineHeight: 1.5 }}>
              All 5 procurement workflow stages (Gate Verification, Physical QC, AI Visual Inspection, Weighbridge Scale, and DBT Clearance) have been completed and audited. DBT payment has been authorized.
            </p>

            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 20px',
              background: 'rgba(59, 130, 246, 0.08)',
              borderRadius: '10px',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              marginBottom: '26px',
              textAlign: 'left'
            }}>
              <Warehouse size={22} color="#3b82f6" />
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#1e40af' }}>
                  Warehouse Storage Physical Check
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                  {storageLot?.is_verified ? (
                    <span style={{ color: '#10b981', fontWeight: 700 }}>
                      ✓ Storage Verified: Checked by {storageLot.storage_employee} ({storageLot.warehouse_name})
                    </span>
                  ) : (
                    <span>Produce cleared at yard gate. Dedicated storage inspection can now be performed in warehouse.</span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-secondary"
                onClick={() => navigate('centre-dashboard')}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', fontSize: '0.92rem', fontWeight: 700 }}
              >
                <ArrowLeft size={16} /> Return to Appointments / Lots Page
              </button>

              <button
                className="btn btn-primary"
                onClick={() => navigate('centre-storage', { appointmentId })}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', fontSize: '0.92rem', fontWeight: 700, background: '#2563eb', borderColor: '#1d4ed8' }}
              >
                <Warehouse size={16} /> Storage Page →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* VERIFIED PROCESS EVIDENCE GALLERY */}
      {evidenceList.length > 0 && (
        <div className="card shadow-sm" style={{ padding: '24px', borderRadius: '14px', background: 'var(--bg-card)', marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <ImageIcon size={20} color="var(--primary)" />
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)' }}>
              Verified Multi-Stage Process Photo Evidence ({evidenceList.length})
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            {evidenceList.map((ev, i) => (
              <div
                key={i}
                style={{
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  overflow: 'hidden',
                  background: 'var(--bg-page)'
                }}
              >
                <img
                  src={ev.file_path}
                  alt={ev.evidence_type}
                  style={{ width: '100%', height: '140px', objectFit: 'cover', display: 'block' }}
                />
                <div style={{ padding: '10px', fontSize: '0.8rem' }}>
                  <span className="badge" style={{ background: '#3b82f6', color: '#fff', fontSize: '0.7rem', marginBottom: '4px' }}>
                    {ev.evidence_type}
                  </span>
                  <div style={{ fontWeight: 700, color: 'var(--secondary)', marginTop: '2px' }}>{ev.process_step}</div>
                  <div style={{ color: 'var(--muted)', fontSize: '0.72rem' }}>By: {ev.uploaded_by}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AUDITED CORRECTION MODAL */}
      {showCorrectionModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '28px', borderRadius: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={20} color="#f59e0b" />
                <h3 style={{ margin: 0, fontWeight: 800, color: 'var(--secondary)' }}>Request Audited Step Correction</h3>
              </div>
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setShowCorrectionModal(false)}
                style={{ padding: '4px 8px' }}
              >
                <X size={16} />
              </button>
            </div>

            <p style={{ color: 'var(--muted)', fontSize: '0.85rem', marginBottom: '18px' }}>
              Completed steps are immutable. Any correction is appended as an audited revision preserving previous values, employee ID, and mandatory rationale.
            </p>

            {correctionMsg && (
              <div className="alert alert-success" style={{ marginBottom: '16px' }}>{correctionMsg}</div>
            )}

            <form onSubmit={handleSubmitCorrection}>
              <div className="form-group" style={{ marginBottom: '14px' }}>
                <label className="form-label">Target Process Step</label>
                <select
                  className="form-control"
                  value={correctionForm.step_number}
                  onChange={e => setCorrectionForm({ ...correctionForm, step_number: parseInt(e.target.value, 10) })}
                >
                  <option value={1}>Step 1: Collection / Intake</option>
                  <option value={2}>Step 2: Physical Quality Inspection</option>
                  <option value={3}>Step 3: Visual Inspection</option>
                  <option value={4}>Step 4: Weighment</option>
                  <option value={5}>Step 5: Procurement Settlement</option>
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: '14px' }}>
                <label className="form-label">Field Name</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. moisture_content_pct, gross_weight_quintals"
                  value={correctionForm.field_name}
                  onChange={e => setCorrectionForm({ ...correctionForm, field_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '14px' }}>
                <label className="form-label">Corrected New Value</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter accurate reading"
                  value={correctionForm.new_value}
                  onChange={e => setCorrectionForm({ ...correctionForm, new_value: e.target.value })}
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label className="form-label">Mandatory Correction Justification</label>
                <textarea
                  className="form-control"
                  rows="3"
                  placeholder="Explain why this change is needed and reference instrument calibration certificate or physical logbook."
                  value={correctionForm.correction_reason}
                  onChange={e => setCorrectionForm({ ...correctionForm, correction_reason: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setShowCorrectionModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submittingCorrection}
                  style={{ background: '#f59e0b', borderColor: '#f59e0b' }}
                >
                  {submittingCorrection ? <RefreshCw size={14} className="spin" /> : <ShieldAlert size={14} />}
                  Submit Audited Correction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
