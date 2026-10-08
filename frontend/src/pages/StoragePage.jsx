import React, { useState, useEffect, useRef } from 'react';
import {
  getProcurementProcessState,
  submitStorageFinalCheck,
  uploadProcessStepEvidence,
  getCentreEmployees
} from '../services/api';
import {
  Warehouse, CheckCircle2, AlertCircle, ArrowLeft, Camera, RefreshCw,
  Clock, ShieldCheck, UserCheck, FileCheck, Layers, Thermometer, Box
} from 'lucide-react';

export default function StoragePage({ user, appointmentId, navigate }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [stateData, setStateData] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  // Form State
  const [storageLotId, setStorageLotId] = useState('');
  const [warehouseName, setWarehouseName] = useState('Central Godown Bay A-1');
  const [stackNumber, setStackNumber] = useState('Stack 04');
  const [receivedQty, setReceivedQty] = useState('');
  const [selectedEmpCode, setSelectedEmpCode] = useState('');
  const [storageCondition, setStorageCondition] = useState('Optimal Humidity & Temperature');
  const [physicalCondition, setPhysicalCondition] = useState('Intact - No Infestation / Good Stacking');
  const [remarks, setRemarks] = useState('');

  // Evidence capture state
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [evidencePreview, setEvidencePreview] = useState(null);
  const [cameraActive, setCameraActive] = useState(false);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);

  const loadData = async () => {
    if (!appointmentId) {
      setError('No appointment ID provided.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await getProcurementProcessState(appointmentId);
      if (res && res.success) {
        setStateData(res);
        const appt = res.appointment;
        const sLot = res.storage_lot;

        // Auto-fill quantity from Step 4 or Step 5
        const netWeight = res.steps?.find(s => s.step_number === 4)?.data?.net_weight_quintals ||
                          appt?.booked_quantity || '';
        setReceivedQty(String(sLot?.quantity_quintals || netWeight || ''));

        if (sLot) {
          setStorageLotId(sLot.lot_id || '');
          if (sLot.warehouse_name) setWarehouseName(sLot.warehouse_name);
          if (sLot.stack_number) setStackNumber(sLot.stack_number);
          if (sLot.storage_condition) setStorageCondition(sLot.storage_condition);
          if (sLot.physical_condition) setPhysicalCondition(sLot.physical_condition);
          if (sLot.remarks) setRemarks(sLot.remarks);
        }

        // Fetch centre employees
        const centreId = appt?.centre_id || user?.centre_id || 'CENTRE-GOA-01';
        try {
          const emps = await getCentreEmployees(centreId);
          setEmployees(emps || []);
          if (emps && emps.length > 0) {
            // Find employee with Storage Supervisor role or default to first
            const storageEmp = emps.find(e => (e.role || '').toLowerCase().includes('storage')) || emps[emps.length - 1];
            setSelectedEmpCode(storageEmp ? storageEmp.employee_code : emps[0].employee_code);
          }
        } catch (e) {
          console.warn('Could not load employees:', e);
        }
      } else {
        setError('Failed to load storage details for this appointment.');
      }
    } catch (err) {
      setError(err.message || 'Error fetching storage details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [appointmentId]);

  // Handle Photo Upload
  const handleSelectFile = (file) => {
    if (!file) return;
    setEvidenceFile(file);
    const r = new FileReader();
    r.onload = () => setEvidencePreview(r.result);
    r.readAsDataURL(file);
  };

  // Camera Capture
  const startCamera = async () => {
    try {
      setCameraActive(true);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (e) {
      alert('Camera access unavailable. Please use file upload.');
      setCameraActive(false);
    }
  };

  const captureCameraPhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg');
    setEvidencePreview(dataUrl);

    canvas.toBlob(blob => {
      if (blob) {
        const file = new File([blob], `storage_${Date.now()}.jpg`, { type: 'image/jpeg' });
        setEvidenceFile(file);
      }
    }, 'image/jpeg');

    // Stop stream
    const stream = videoRef.current.srcObject;
    if (stream) stream.getTracks().forEach(t => t.stop());
    setCameraActive(false);
  };

  const handleSubmitStorageCheck = async (e) => {
    e.preventDefault();
    if (!receivedQty || parseFloat(receivedQty) <= 0) {
      setError('Please enter a valid received quantity in Quintals.');
      return;
    }
    setSubmitting(true);
    setError('');
    setSuccessMsg('');

    try {
      // 1. Upload evidence photo if attached
      let evidenceUrl = null;
      if (evidenceFile) {
        const uploadRes = await uploadProcessStepEvidence(
          appointmentId,
          evidenceFile,
          'STORAGE',
          'STORAGE_FINAL_CHECK',
          `Storage stacking evidence for appointment ${appointmentId}`
        );
        if (uploadRes && uploadRes.file_path) {
          evidenceUrl = uploadRes.file_path;
        }
      }

      // 2. Identify assigned employee
      const assignedEmp = employees.find(e => e.employee_code === selectedEmpCode) || employees[0];
      const empName = assignedEmp ? assignedEmp.name : (user.name || 'Supervisor');
      const empId = assignedEmp ? assignedEmp.employee_code : user.user_id;

      // 3. Submit Storage Final Check
      const payload = {
        received_quantity_quintals: parseFloat(receivedQty),
        storage_employee_name: empName,
        storage_employee_id: empId,
        storage_condition: storageCondition,
        physical_condition: physicalCondition,
        remarks: remarks || `Intake confirmed at ${warehouseName} (${stackNumber}). Atmospheric condition verified.`,
        evidence_url: evidenceUrl
      };

      const res = await submitStorageFinalCheck(appointmentId, payload);
      if (res && res.success) {
        setSuccessMsg('Storage final inspection successfully verified and recorded in the database!');
        await loadData();
      } else {
        setError(res?.detail || 'Failed to record storage final check.');
      }
    } catch (err) {
      setError(err.message || 'Error recording storage final check.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px' }}>
        <RefreshCw size={32} className="spin" color="var(--primary)" style={{ margin: '0 auto 16px auto' }} />
        <h3>Loading Dedicated Storage Record...</h3>
        <p style={{ color: 'var(--muted)' }}>Retrieving lot, warehouse bay, and verified evidence records...</p>
      </div>
    );
  }

  const appt = stateData?.appointment;
  const storageLot = stateData?.storage_lot;
  const isVerified = storageLot?.is_verified || storageLot?.status === 'VERIFIED_STORED';

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px 16px 60px 16px' }}>
      {/* Top Navigation Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <button
            className="btn btn-outline btn-sm"
            onClick={() => navigate('centre-dashboard')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}
          >
            <ArrowLeft size={14} /> Back to Appointments & Lots
          </button>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Warehouse size={28} color="#2563eb" /> Warehouse Storage & Stacking Inspection
          </h1>
          <p style={{ margin: '4px 0 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>
            Dedicated lot intake inspection, atmospheric temperature/humidity check, and immutable storage audit.
          </p>
        </div>

        {isVerified ? (
          <span className="badge badge-confirmed" style={{ padding: '8px 14px', fontSize: '0.9rem', fontWeight: 800 }}>
            <CheckCircle2 size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} /> STORAGE VERIFIED & AUDITED
          </span>
        ) : (
          <span className="badge badge-pending" style={{ padding: '8px 14px', fontSize: '0.9rem', fontWeight: 800 }}>
            <Clock size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} /> PENDING PHYSICAL STORAGE CHECK
          </span>
        )}
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertCircle size={20} />
          <div>{error}</div>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <CheckCircle2 size={20} />
          <div>{successMsg}</div>
        </div>
      )}

      {/* Appointment & Lot Metadata Banner */}
      <div className="card shadow-sm" style={{ padding: '22px', borderRadius: '12px', background: 'var(--bg-card)', marginBottom: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: '0 0 14px 0', color: 'var(--secondary)', borderBottom: '1px solid var(--border)', paddingBottom: '10px' }}>
          Appointment & Procurement Reference
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '0.9rem' }}>
          <div>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem', display: 'block' }}>APPOINTMENT CODE</span>
            <strong style={{ fontSize: '1.05rem', color: 'var(--primary)' }}>{appt?.appointment_id || appointmentId}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem', display: 'block' }}>FARMER NAME</span>
            <strong>{appt?.farmer_name}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem', display: 'block' }}>COMMODITY / REGION</span>
            <strong>{appt?.crop} ({appt?.state || 'Goa'})</strong>
          </div>
          <div>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem', display: 'block' }}>PROCURED NET QUANTITY</span>
            <strong style={{ color: 'var(--success-text)' }}>{receivedQty || appt?.booked_quantity} Quintals</strong>
          </div>
          <div>
            <span style={{ color: 'var(--muted)', fontSize: '0.8rem', display: 'block' }}>PROCUREMENT CENTRE</span>
            <strong>{appt?.centre_name || appt?.centre_id}</strong>
          </div>
        </div>
      </div>

      {/* VERIFIED STORAGE DETAILS CARD */}
      {isVerified && storageLot && (
        <div className="card shadow-sm" style={{ padding: '26px', borderRadius: '14px', background: 'var(--success-bg)', border: '2px solid var(--primary)', marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '18px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: 'var(--primary)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={26} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: 'var(--success-text)' }}>
                Storage Lot Audit Record Verified
              </h3>
              <p style={{ margin: '2px 0 0 0', color: 'var(--success-text)', fontSize: '0.85rem' }}>
                Produce has been placed in warehouse stacks and verified by authorized storage personnel.
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', background: 'var(--bg-card)', padding: '18px', borderRadius: '10px', border: '1px solid var(--border)' }}>
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'block' }}>STORAGE LOT ID</span>
              <strong style={{ fontSize: '1.1rem', color: 'var(--secondary)' }}>{storageLot.lot_id}</strong>
            </div>
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'block' }}>WAREHOUSE & STACK</span>
              <strong>{storageLot.warehouse_name || warehouseName} ({storageLot.stack_number || stackNumber})</strong>
            </div>
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'block' }}>VERIFIED QUANTITY</span>
              <strong style={{ color: 'var(--success-text)' }}>{storageLot.quantity_quintals} Quintals</strong>
            </div>
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'block' }}>VERIFIED BY EMPLOYEE</span>
              <strong style={{ color: 'var(--secondary)' }}>{storageLot.storage_employee || selectedEmpCode}</strong>
            </div>
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'block' }}>ATMOSPHERIC CONDITION</span>
              <strong>{storageLot.storage_condition}</strong>
            </div>
            <div>
              <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'block' }}>PHYSICAL INTEGRITY</span>
              <strong>{storageLot.physical_condition}</strong>
            </div>
          </div>

          {storageLot.remarks && (
            <div style={{ marginTop: '16px', background: 'var(--bg-card)', padding: '14px', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.88rem' }}>
              <strong>Supervisor Remarks:</strong> <em>"{storageLot.remarks}"</em>
            </div>
          )}

          {/* Existing Evidence Photos */}
          {stateData?.evidence?.filter(ev => ev.evidence_type === 'STORAGE' || ev.process_step === 'STORAGE_FINAL_CHECK').length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 10px 0', color: 'var(--secondary)' }}>
                Audited Storage Stack Evidence
              </h4>
              <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                {stateData.evidence.filter(ev => ev.evidence_type === 'STORAGE' || ev.process_step === 'STORAGE_FINAL_CHECK').map((ev, idx) => (
                  <div key={idx} style={{ textAlign: 'center' }}>
                    <img
                      src={ev.file_path}
                      alt="Storage Stack Evidence"
                      style={{ width: '130px', height: '110px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--border)' }}
                    />
                    <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '4px' }}>
                      By {ev.uploaded_by}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* INDEPENDENT STORAGE FINAL CHECK FORM */}
      {(!isVerified || !storageLot) && (
        <form onSubmit={handleSubmitStorageCheck} className="card shadow-sm" style={{ padding: '28px', borderRadius: '14px', background: 'var(--bg-card)', border: '2px solid #3b82f6' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '16px', marginBottom: '24px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '50%', background: '#3b82f6', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Warehouse size={24} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, color: 'var(--secondary)' }}>
                Independent Storage Final Check Form
              </h3>
              <p style={{ margin: '2px 0 0 0', color: 'var(--muted)', fontSize: '0.85rem' }}>
                Conduct independent physical check of produce received into storage, verify bay placement, and record photographic evidence.
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px', marginBottom: '20px' }}>
            {/* Storage Employee Dropdown (from DB) */}
            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 700 }}>
                <UserCheck size={15} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Storage Supervisor Employee *
              </label>
              <select
                className="form-control"
                value={selectedEmpCode}
                onChange={e => setSelectedEmpCode(e.target.value)}
                required
              >
                {employees.map(emp => (
                  <option key={emp.employee_code || emp.id} value={emp.employee_code}>
                    {emp.name} ({emp.employee_code})
                  </option>
                ))}
              </select>
              <small style={{ color: 'var(--muted)' }}>Employee must be active in centre database roster.</small>
            </div>

            {/* Warehouse Bay / Stack */}
            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 700 }}>
                <Warehouse size={15} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Warehouse Name / Godown
              </label>
              <input
                type="text"
                className="form-control"
                value={warehouseName}
                onChange={e => setWarehouseName(e.target.value)}
                required
              />
            </div>

            {/* Stack Number */}
            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 700 }}>
                <Layers size={15} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Stack / Pallet Number
              </label>
              <input
                type="text"
                className="form-control"
                value={stackNumber}
                onChange={e => setStackNumber(e.target.value)}
                required
              />
            </div>

            {/* Received Stored Quantity */}
            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 700 }}>
                <Box size={15} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Verified Stored Quantity (Quintals) *
              </label>
              <input
                type="number"
                step="0.01"
                min="0.1"
                className="form-control"
                value={receivedQty}
                onChange={e => setReceivedQty(e.target.value)}
                required
              />
              <small style={{ color: 'var(--muted)' }}>Actual scale quantity physically placed on stack</small>
            </div>

            {/* Storage Condition */}
            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 700 }}>
                <Thermometer size={15} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Storage Atmosphere / Ambient Condition *
              </label>
              <select
                className="form-control"
                value={storageCondition}
                onChange={e => setStorageCondition(e.target.value)}
                required
              >
                <option value="Optimal Humidity & Temperature">Optimal Humidity & Temperature (Standard)</option>
                <option value="Cool Dry Aerated Storage">Cool Dry Aerated Storage (12-14°C)</option>
                <option value="Controlled Atmosphere Cold Storage">Controlled Atmosphere Cold Storage</option>
                <option value="Ambient Ventilated Silo">Ambient Ventilated Silo (&lt;13% Moisture)</option>
                <option value="Slight Moisture Risk - Aeration Needed">Slight Moisture Risk - Aeration Needed</option>
                <option value="High Temperature - Priority Evacuation">High Temperature - Priority Evacuation</option>
              </select>
            </div>

            {/* Physical Condition */}
            <div className="form-group">
              <label className="form-label" style={{ fontWeight: 700 }}>
                <FileCheck size={15} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                Produce Physical Inspection Result *
              </label>
              <select
                className="form-control"
                value={physicalCondition}
                onChange={e => setPhysicalCondition(e.target.value)}
                required
              >
                <option value="Intact - No Infestation / Good Stacking">Intact - No Infestation / Good Stacking</option>
                <option value="Clean Dry Grain - Standard Stack">Clean Dry Grain - Standard Stack</option>
                <option value="Minor Bag Abrasion - Produce Sound">Minor Bag Abrasion - Produce Sound</option>
                <option value="Moisture Stained - Monitor Daily">Moisture Stained - Monitor Daily</option>
                <option value="Infested / Damaged - Quarantine">Infested / Damaged - Quarantine</option>
              </select>
            </div>
          </div>

          {/* Photo Evidence Capture */}
          <div style={{ background: 'var(--bg-page)', padding: '18px 20px', borderRadius: '10px', border: '1px solid var(--border)', marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: 'var(--secondary)' }}>
                  Storage Stack Photo Evidence
                </h4>
                <p style={{ margin: '2px 0 0 0', color: 'var(--muted)', fontSize: '0.8rem' }}>
                  Capture photograph of produce lot safely placed in warehouse stack or bay.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  accept="image/*"
                  onChange={e => handleSelectFile(e.target.files?.[0])}
                />
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => fileInputRef.current?.click()}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Camera size={14} /> Upload Stack Photo
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={startCamera}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Camera size={14} /> Use Camera
                </button>
              </div>
            </div>

            {/* Camera Viewfinder */}
            {cameraActive && (
              <div style={{ marginBottom: '14px', textAlign: 'center' }}>
                <video ref={videoRef} autoPlay playsInline style={{ width: '100%', maxWidth: '400px', borderRadius: '8px', border: '2px solid var(--primary)' }} />
                <div style={{ marginTop: '8px' }}>
                  <button type="button" className="btn btn-primary btn-sm" onClick={captureCameraPhoto}>
                    📸 Grab Photo
                  </button>
                </div>
              </div>
            )}

            {/* Thumbnail Preview */}
            {evidencePreview && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <img
                  src={evidencePreview}
                  alt="Storage Stack Preview"
                  style={{ width: '90px', height: '80px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--border)' }}
                />
                <div style={{ fontSize: '0.85rem', color: 'var(--success-text)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={16} /> Stack evidence photo attached ({evidenceFile?.name || 'camera_capture.jpg'})
                </div>
              </div>
            )}
          </div>

          {/* Supervisor Remarks */}
          <div className="form-group" style={{ marginBottom: '24px' }}>
            <label className="form-label" style={{ fontWeight: 700 }}>Storage Officer Remarks & Notes</label>
            <textarea
              className="form-control"
              rows="3"
              placeholder="Record exact stack placement, aeration conditions, dunnage verification, bag count..."
              value={remarks}
              onChange={e => setRemarks(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '14px' }}>
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => navigate('centre-dashboard')}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 28px', fontSize: '1rem', fontWeight: 700, backgroundColor: '#2563eb' }}
            >
              {submitting ? <RefreshCw size={18} className="spin" /> : <ShieldCheck size={18} />}
              Verify & Record Final Storage Check
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
