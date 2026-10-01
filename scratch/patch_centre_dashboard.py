import re

with open('frontend/src/pages/CentreDashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. State addition after procurementError
evidence_state_code = '''  const [procurementError, setProcurementError] = useState('');

  // Photo Evidence State (Quality, Weighing, Moisture)
  const [bookingEvidence, setBookingEvidence] = useState({ QUALITY: [], WEIGHING: [], MOISTURE: [] });
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [evidenceUploadStatus, setEvidenceUploadStatus] = useState({
    QUALITY: { uploading: false, error: '', success: '' },
    WEIGHING: { uploading: false, error: '', success: '' },
    MOISTURE: { uploading: false, error: '', success: '' }
  });
  const [pendingFiles, setPendingFiles] = useState({
    QUALITY: null,
    WEIGHING: null,
    MOISTURE: null
  });
  const [filePreviews, setFilePreviews] = useState({
    QUALITY: null,
    WEIGHING: null,
    MOISTURE: null
  });
  const [enlargedImage, setEnlargedImage] = useState(null);

  const loadBookingEvidence = async (numericBookingId) => {
    if (!numericBookingId) return;
    setLoadingEvidence(true);
    try {
      const res = await getProcurementEvidence(numericBookingId);
      if (res && res.by_type) {
        setBookingEvidence({
          QUALITY: res.by_type.QUALITY || [],
          WEIGHING: res.by_type.WEIGHING || [],
          MOISTURE: res.by_type.MOISTURE || []
        });
      }
    } catch (e) {
      console.warn('Could not load evidence for booking:', e);
    } finally {
      setLoadingEvidence(false);
    }
  };

  const handleSelectEvidenceFile = (type, file) => {
    if (!file) return;
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type.toLowerCase())) {
      setEvidenceUploadStatus(prev => ({
        ...prev,
        [type]: { uploading: false, error: 'Only JPG, PNG, and WEBP images are supported.', success: '' }
      }));
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setEvidenceUploadStatus(prev => ({
        ...prev,
        [type]: { uploading: false, error: 'File size must be 5MB or less.', success: '' }
      }));
      return;
    }

    if (filePreviews[type]) {
      try { URL.revokeObjectURL(filePreviews[type]); } catch (e) {}
    }
    const previewUrl = URL.createObjectURL(file);
    setPendingFiles(prev => ({ ...prev, [type]: file }));
    setFilePreviews(prev => ({ ...prev, [type]: previewUrl }));
    setEvidenceUploadStatus(prev => ({
      ...prev,
      [type]: { uploading: false, error: '', success: '' }
    }));
  };

  const handleClearPendingFile = (type) => {
    if (filePreviews[type]) {
      try { URL.revokeObjectURL(filePreviews[type]); } catch (e) {}
    }
    setPendingFiles(prev => ({ ...prev, [type]: null }));
    setFilePreviews(prev => ({ ...prev, [type]: null }));
    setEvidenceUploadStatus(prev => ({
      ...prev,
      [type]: { uploading: false, error: '', success: '' }
    }));
  };

  const handleUploadSingleEvidence = async (type, numericBookingId) => {
    const file = pendingFiles[type];
    if (!file || !numericBookingId) return;

    setEvidenceUploadStatus(prev => ({
      ...prev,
      [type]: { uploading: true, error: '', success: '' }
    }));

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('booking_id', String(numericBookingId));
      formData.append('evidence_type', type);
      formData.append('notes', `${type} photo measurement captured at mandi`);

      const res = await uploadProcurementEvidence(formData);
      if (res.success) {
        handleClearPendingFile(type);
        setEvidenceUploadStatus(prev => ({
          ...prev,
          [type]: { uploading: false, error: '', success: `${type} photo uploaded successfully!` }
        }));
        await loadBookingEvidence(numericBookingId);
      } else {
        throw new Error(res.message || 'Upload failed');
      }
    } catch (err) {
      setEvidenceUploadStatus(prev => ({
        ...prev,
        [type]: { uploading: false, error: err.message || 'Failed to upload photo', success: '' }
      }));
    }
  };'''

content = content.replace("  const [procurementError, setProcurementError] = useState('');", evidence_state_code, 1)

# 2. Update handleOpenProcurementModal to load evidence and reset pending files
old_modal_open = '''  const handleOpenProcurementModal = async (b) => {
    setSelectedArrivedBooking(b);
    setWorkflowRecordIds({ collection_id: null, check_id: null, weighment_id: null, payment_id: null });'''

new_modal_open = '''  const handleOpenProcurementModal = async (b) => {
    setSelectedArrivedBooking(b);
    setWorkflowRecordIds({ collection_id: null, check_id: null, weighment_id: null, payment_id: null });
    const rawBkId = b.id !== undefined && b.id !== null ? b.id : b.booking_id;
    const numBkId = typeof rawBkId === 'number' ? rawBkId : parseInt(rawBkId, 10);
    setPendingFiles({ QUALITY: null, WEIGHING: null, MOISTURE: null });
    setFilePreviews({ QUALITY: null, WEIGHING: null, MOISTURE: null });
    setEvidenceUploadStatus({
      QUALITY: { uploading: false, error: '', success: '' },
      WEIGHING: { uploading: false, error: '', success: '' },
      MOISTURE: { uploading: false, error: '', success: '' }
    });
    if (!isNaN(numBkId) && numBkId > 0) {
      loadBookingEvidence(numBkId);
    }'''

content = content.replace(old_modal_open, new_modal_open, 1)

# 3. Update handleProcessWorkflowStep to auto-upload selected evidence (optional)
old_qc_step = '''      } else if (targetStatus === 'QUALITY_CHECKED') {
        const qcRes = await recordQualityCheck({'''

new_qc_step = '''      } else if (targetStatus === 'QUALITY_CHECKED') {
        // Auto-upload optional quality & moisture evidence if selected
        if (pendingFiles.QUALITY) {
          try { await handleUploadSingleEvidence('QUALITY', numericBookingId); } catch (e) { console.warn(e); }
        }
        if (pendingFiles.MOISTURE) {
          try { await handleUploadSingleEvidence('MOISTURE', numericBookingId); } catch (e) { console.warn(e); }
        }
        const qcRes = await recordQualityCheck({'''

content = content.replace(old_qc_step, new_qc_step, 1)

old_wb_step = '''      } else if (targetStatus === 'WEIGHED') {
        const gross = parseFloat(procurementForm.actual_weight || procurementForm.actual_quantity || selectedArrivedBooking.quantity);'''

new_wb_step = '''      } else if (targetStatus === 'WEIGHED') {
        // Auto-upload optional weighing evidence if selected
        if (pendingFiles.WEIGHING) {
          try { await handleUploadSingleEvidence('WEIGHING', numericBookingId); } catch (e) { console.warn(e); }
        }
        const gross = parseFloat(procurementForm.actual_weight || procurementForm.actual_quantity || selectedArrivedBooking.quantity);'''

content = content.replace(old_wb_step, new_wb_step, 1)

# 4. QR verification token check: use centreId instead of user.user_id
content = content.replace("const res = await verifyQrToken(tokenToVerify.trim(), user.user_id);",
                          "const res = await verifyQrToken(tokenToVerify.trim(), centreId);")

# 5. QR result details card background
content = content.replace("backgroundColor: 'white', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', color: 'var(--secondary)'",
                          "backgroundColor: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', color: 'var(--secondary)'")

# 6. Centre header info circles
content = content.replace("backgroundColor: '#e0f2fe', color: '#0284c7'",
                          "backgroundColor: 'var(--info-bg)', color: 'var(--info-text)'")
content = content.replace("backgroundColor: '#f0fdf4', color: '#16a34a'",
                          "backgroundColor: 'var(--success-bg)', color: 'var(--success-text)'")
content = content.replace("color: '#15803d' }}>\n              {dailyCapacityInfo.max_quintals_per_day}",
                          "color: 'var(--primary)' }}>\n              {dailyCapacityInfo.max_quintals_per_day}")

# 7. Universal date bar
content = content.replace("style={{ padding: '16px 24px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px' }}",
                          "style={{ padding: '16px 24px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px' }}")
content = content.replace("color: 'var(--primary-dark)', background: '#e0f2fe', padding: '6px 14px', borderRadius: '20px'",
                          "color: 'var(--info-text)', background: 'var(--info-bg)', padding: '6px 14px', borderRadius: '20px'")

# 8. Closed date card (Overview)
content = content.replace("background: '#fef2f2', border: '1.5px solid #fca5a5', borderRadius: '14px'",
                          "background: 'var(--danger-bg)', border: '1.5px solid var(--danger)', borderRadius: '14px'")
content = content.replace("backgroundColor: '#fee2e2', color: '#dc2626'",
                          "backgroundColor: 'var(--danger-bg)', color: 'var(--danger)'")
content = content.replace("color: '#991b1b', fontWeight: 800, marginBottom: '8px'",
                          "color: 'var(--danger-text)', fontWeight: 800, marginBottom: '8px'")
content = content.replace("color: '#b91c1c', fontWeight: 600, margin: 0",
                          "color: 'var(--danger-text)', fontWeight: 600, margin: 0")

# 9. No schedule card (Overview)
content = content.replace("style={{ padding: '32px', textAlign: 'center', background: '#fafafa', border: '1px dashed var(--border)', borderRadius: '14px' }}",
                          "style={{ padding: '32px', textAlign: 'center', background: 'var(--bg-card)', border: '1px dashed var(--border)', borderRadius: '14px' }}")

# 10. Crop summary empty box & table
content = content.replace("padding: '24px', background: '#fafafa', borderRadius: '8px', border: '1px dashed #e2e8f0'",
                          "padding: '24px', background: 'var(--bg-page)', borderRadius: '8px', border: '1px dashed var(--border)'")
content = content.replace("<tr style={{ background: '#f8fafc' }}>",
                          "<tr style={{ background: 'var(--bg-page)' }}>")
content = content.replace("<tr style={{ background: '#f0fdf4', borderTop: '2px solid #bbf7d0' }}>",
                          "<tr style={{ background: 'var(--success-bg)', borderTop: '2px solid var(--primary-border)' }}>")
content = content.replace("color: '#14532d', padding: '14px 16px'",
                          "color: 'var(--success-text)', padding: '14px 16px'")
content = content.replace("color: '#16a34a', padding: '14px 16px'",
                          "color: 'var(--primary)', padding: '14px 16px'")

# 11. Appointments tab
content = content.replace("color: 'var(--primary-dark)', background: '#e0f2fe', padding: '6px 12px', borderRadius: '8px'",
                          "color: 'var(--info-text)', background: 'var(--info-bg)', padding: '6px 12px', borderRadius: '8px'")
content = content.replace("padding: '32px', background: '#fef2f2', borderRadius: '12px', border: '1px solid #fca5a5'",
                          "padding: '32px', background: 'var(--danger-bg)', borderRadius: '12px', border: '1px solid var(--danger)'")
content = content.replace("<h3 style={{ color: '#991b1b', fontWeight: 800 }}>Centre Closed",
                          "<h3 style={{ color: 'var(--danger-text)', fontWeight: 800 }}>Centre Closed")
content = content.replace("<p style={{ color: '#b91c1c' }}>Reason:",
                          "<p style={{ color: 'var(--danger-text)' }}>Reason:")
content = content.replace("padding: '36px', background: '#fafafa', borderRadius: '12px', border: '1px dashed #cbd5e1'",
                          "padding: '36px', background: 'var(--bg-page)', borderRadius: '12px', border: '1px dashed var(--border)'")
content = content.replace("style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}",
                          "style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}")
content = content.replace("style={{ background: '#f8fafc', padding: '14px 20px', borderBottom: '1px solid #e2e8f0'",
                          "style={{ background: 'var(--bg-page)', padding: '14px 20px', borderBottom: '1px solid var(--border)'")
content = content.replace("color: slot.is_full ? '#dc2626' : '#15803d'",
                          "color: slot.is_full ? 'var(--danger)' : 'var(--primary)'")
content = content.replace("style={{ backgroundColor: '#e0f2fe', color: '#0369a1', borderColor: '#7dd3fc' }}",
                          "style={{ backgroundColor: 'var(--info-bg)', color: 'var(--info-text)', borderColor: 'var(--info)' }}")

# 12. Slots tab
content = content.replace("background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',\n            border: '1px solid #bbf7d0',",
                          "background: 'var(--success-bg)',\n            border: '1px solid var(--primary-border)',")
content = content.replace("color: '#166534', fontWeight: 700, textTransform: 'uppercase'",
                          "color: 'var(--success-text)', fontWeight: 700, textTransform: 'uppercase'")
content = content.replace("color: '#14532d', marginTop: '4px'",
                          "color: 'var(--success-text)', marginTop: '4px'")
content = content.replace("color: '#15803d', marginTop: '2px'",
                          "color: 'var(--primary)', marginTop: '2px'")

# 13. Config tab
content = content.replace("background: isChecked ? '#f0fdf4' : '#f8fafc', border: `1px solid ${isChecked ? '#bbf7d0' : '#e2e8f0'}`",
                          "background: isChecked ? 'var(--success-bg)' : 'var(--bg-page)', border: `1px solid ${isChecked ? 'var(--primary-border)' : 'var(--border)'}`")
content = content.replace("color: isChecked ? '#166534' : 'var(--text-secondary)'",
                          "color: isChecked ? 'var(--success-text)' : 'var(--text-secondary)'")
content = content.replace("color: '#16a34a', textTransform: 'uppercase' }}>Open",
                          "color: 'var(--success)', textTransform: 'uppercase' }}>Open")
content = content.replace("color: '#dc2626', textTransform: 'uppercase' }}>Closed",
                          "color: 'var(--danger)', textTransform: 'uppercase' }}>Closed")
content = content.replace("style={{ marginBottom: '20px', background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}",
                          "style={{ marginBottom: '20px', background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)' }}")
content = content.replace("padding: '16px', background: '#fafafa', borderRadius: '8px'",
                          "padding: '16px', background: 'var(--bg-page)', borderRadius: '8px', border: '1px solid var(--border)'")
content = content.replace("padding: '10px 14px', background: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca'",
                          "padding: '10px 14px', background: 'var(--danger-bg)', borderRadius: '8px', border: '1px solid var(--danger)'")
content = content.replace("color: '#991b1b', fontSize: '0.9rem'",
                          "color: 'var(--danger-text)', fontSize: '0.9rem'")
content = content.replace("color: '#b91c1c' }}>{item.reason}",
                          "color: 'var(--danger-text)' }}>{item.reason}")

# 14. Date range modal highlight
content = content.replace("background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '12px', borderRadius: '8px'",
                          "background: 'var(--success-bg)', border: '1px solid var(--primary-border)', padding: '12px', borderRadius: '8px'")

with open('frontend/src/pages/CentreDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch 1 applied successfully!")
