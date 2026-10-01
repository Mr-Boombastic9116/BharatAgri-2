import sys

with open('frontend/src/pages/CentreDashboard.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's check if renderEvidenceSection is already defined
if 'const renderEvidenceSection' not in content:
    # We will add renderEvidenceSection right above return (
    evidence_helper = '''  const renderEvidenceSection = (type, title, description) => {
    const rawBkId = selectedArrivedBooking?.id ?? selectedArrivedBooking?.booking_id;
    const currentBookingId = typeof rawBkId === 'number' ? rawBkId : parseInt(rawBkId, 10);
    const existingList = bookingEvidence[type] || [];
    const pendingFile = pendingFiles[type];
    const previewUrl = filePreviews[type];
    const status = evidenceUploadStatus[type];

    return (
      <div className="evidence-section" style={{
        marginTop: '0.75rem',
        padding: '0.85rem',
        borderRadius: 'var(--radius-sm)',
        background: 'var(--bg-page)',
        border: '1px solid var(--border)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div>
            <strong style={{ fontSize: '0.85rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ImageIcon size={15} style={{ color: 'var(--primary)' }} />
              {title}
            </strong>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted)', display: 'block' }}>
              {description} <em style={{ fontStyle: 'normal', color: 'var(--primary)', fontWeight: 600 }}>(Optional)</em>
            </span>
          </div>
          {existingList.length > 0 && (
            <span className="badge badge-confirmed" style={{ fontSize: '0.7rem' }}>
              <FileCheck size={12} style={{ marginRight: '4px' }} /> {existingList.length} Uploaded
            </span>
          )}
        </div>

        {/* Existing uploaded evidence thumbnails */}
        {existingList.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
            {existingList.map((ev, idx) => (
              <div 
                key={ev.id || idx}
                style={{
                  position: 'relative',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  background: 'var(--bg-card)'
                }}
                onClick={() => setEnlargedImage(ev.file_path || ev.file_url)}
                title="Click to enlarge"
              >
                <img 
                  src={ev.file_path || ev.file_url} 
                  alt={ev.original_filename || `${type} Evidence`} 
                  style={{ width: '70px', height: '70px', objectFit: 'cover', display: 'block' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  background: 'rgba(0,0,0,0.6)',
                  color: '#fff',
                  fontSize: '0.62rem',
                  padding: '2px 4px',
                  textAlign: 'center',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap'
                }}>
                  {ev.original_filename || `Evidence #${idx+1}`}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic', marginBottom: '0.5rem' }}>
            No evidence uploaded yet
          </div>
        )}

        {/* File selection & preview */}
        {previewUrl ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.5rem',
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--primary-border)',
            marginBottom: '0.5rem'
          }}>
            <img 
              src={previewUrl} 
              alt="Selected Preview" 
              style={{ width: '56px', height: '56px', objectFit: 'cover', borderRadius: '4px', border: '1px solid var(--border)' }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {pendingFile?.name}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                {(pendingFile?.size / 1024).toFixed(1)} KB • Ready to save
              </div>
            </div>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                type="button"
                className="btn btn-primary"
                style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                disabled={status.uploading}
                onClick={() => handleUploadSingleEvidence(type, currentBookingId)}
              >
                {status.uploading ? 'Uploading...' : 'Upload Now'}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                onClick={() => handleClearPendingFile(type)}
                disabled={status.uploading}
              >
                <X size={14} />
              </button>
            </div>
          </div>
        ) : (
          <label style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--border)',
            background: 'var(--bg-card)',
            color: 'var(--secondary)',
            fontSize: '0.78rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}>
            <Upload size={14} style={{ color: 'var(--primary)' }} />
            <span>Select {title.split(' ')[0]} Photo (JPG/PNG/WEBP, Max 5MB)</span>
            <input 
              type="file" 
              accept="image/jpeg,image/png,image/webp" 
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleSelectEvidenceFile(type, e.target.files[0]);
                }
              }}
            />
          </label>
        )}

        {/* Status messages */}
        {status.error && (
          <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--danger-text)' }}>
            ⚠ {status.error}
          </div>
        )}
        {status.success && (
          <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--success-text)' }}>
            ✓ {status.success}
          </div>
        )}
      </div>
    );
  };

  return ('''
    content = content.replace("  return (", evidence_helper, 1)

# Now replace the price breakdown in the modal to fix dark mode
old_price_breakdown = '''              {/* Price Intelligence & Procurement Payment Breakdown (Prompt 2 - Section 12) */}
              <div style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
                textAlign: 'center'
              }}>
                <div style={{ background: '#ffffff', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    MSP Reference Value
                  </span>
                  <strong style={{ fontSize: '1.15rem', color: '#1e293b', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.msp_reference_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: '#64748b' }}>
                    {procurementForm.actual_quantity || 0} Q × ₹{procurementForm.official_msp || 2300}/Q MSP
                  </span>
                </div>

                <div style={{ background: '#ffffff', padding: '10px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <span style={{ fontSize: '0.72rem', color: '#0284c7', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    Estimated Value
                  </span>
                  <strong style={{ fontSize: '1.15rem', color: '#0284c7', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.estimated_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: '#0284c7' }}>
                    {procurementForm.actual_quantity || 0} Q × ₹{procurementForm.estimated_price || 2345}/Q Estimate
                  </span>
                </div>

                <div style={{ background: '#f0fdf4', padding: '10px', borderRadius: '6px', border: '1px solid #bbf7d0' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--success-text)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    Actual Payment
                  </span>
                  <strong style={{ fontSize: '1.2rem', color: '#15803d', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.payment_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: '#166534', fontWeight: 600 }}>
                    Certified Weighed Payout
                  </span>
                </div>
              </div>'''

new_price_breakdown = '''              {/* Price Intelligence & Procurement Payment Breakdown */}
              <div style={{
                background: 'var(--bg-page)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
                textAlign: 'center'
              }}>
                <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    MSP Reference Value
                  </span>
                  <strong style={{ fontSize: '1.15rem', color: 'var(--secondary)', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.msp_reference_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: 'var(--muted)' }}>
                    {procurementForm.actual_quantity || 0} Q × ₹{procurementForm.official_msp || 2300}/Q MSP
                  </span>
                </div>

                <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--info-text)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    Estimated Value
                  </span>
                  <strong style={{ fontSize: '1.15rem', color: 'var(--info-text)', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.estimated_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: 'var(--info-text)' }}>
                    {procurementForm.actual_quantity || 0} Q × ₹{procurementForm.estimated_price || 2345}/Q Estimate
                  </span>
                </div>

                <div style={{ background: 'var(--success-bg)', padding: '10px', borderRadius: '6px', border: '1px solid var(--primary-border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--success-text)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    Actual Payment
                  </span>
                  <strong style={{ fontSize: '1.2rem', color: 'var(--primary)', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.payment_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: 'var(--success-text)', fontWeight: 600 }}>
                    Certified Weighed Payout
                  </span>
                </div>
              </div>'''

content = content.replace(old_price_breakdown, new_price_breakdown, 1)

# Now insert Evidence sections into Step 2 (Quality & Moisture) and Step 3 (Weighing)
old_quality_moisture = '''              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Quality Grade</label>
                  <select
                    className="form-control"
                    value={procurementForm.quality_grade}
                    onChange={(e) => setProcurementForm(f => ({ ...f, quality_grade: e.target.value }))}
                  >
                    <option value="GRADE_A">Grade A (FAQ Premium)</option>
                    <option value="GRADE_B">Grade B (Standard Commercial)</option>
                    <option value="GRADE_C">Grade C (Sub-standard)</option>
                  </select>
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Moisture Content (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.moisture_pct}
                    onChange={(e) => setProcurementForm(f => ({ ...f, moisture_pct: e.target.value }))}
                  />
                </div>
              </div>'''

new_quality_moisture = '''              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Quality Grade</label>
                  <select
                    className="form-control"
                    value={procurementForm.quality_grade}
                    onChange={(e) => setProcurementForm(f => ({ ...f, quality_grade: e.target.value }))}
                  >
                    <option value="GRADE_A">Grade A (FAQ Premium)</option>
                    <option value="GRADE_B">Grade B (Standard Commercial)</option>
                    <option value="GRADE_C">Grade C (Sub-standard)</option>
                  </select>
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Moisture Content (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.moisture_pct}
                    onChange={(e) => setProcurementForm(f => ({ ...f, moisture_pct: e.target.value }))}
                  />
                </div>
              </div>

              {/* Quality Evidence (Section 4) */}
              {renderEvidenceSection('QUALITY', 'Quality Measurement Evidence', 'Photo of inspected sample or physical grading.')}

              {/* Moisture Evidence (Section 6) */}
              {renderEvidenceSection('MOISTURE', 'Moisture Measurement Evidence', 'Photo of digital moisture meter reading.')}'''

content = content.replace(old_quality_moisture, new_quality_moisture, 1)

# Now Weighing Evidence in Weighment section
old_weighing = '''                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Certified Gross Weight (Quintals)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.actual_weight}
                    onChange={(e) => setProcurementForm(f => ({ ...f, actual_weight: e.target.value }))}
                  />
                </div>'''

new_weighing = '''                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Certified Gross Weight (Quintals)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.actual_weight}
                    onChange={(e) => setProcurementForm(f => ({ ...f, actual_weight: e.target.value }))}
                  />
                </div>
              </div>

              {/* Weighing Evidence (Section 5) */}
              {renderEvidenceSection('WEIGHING', 'Weighing Photo Evidence', 'Photo of weighbridge scale or certified tare slip.')}'''

# Note: old_weighing was inside a grid of 2 columns, so replacing the closing div carefully:
content = content.replace(old_weighing + '\n              </div>', new_weighing, 1)

# Also add Enlarged Image modal before the closing tag of the dashboard
enlarged_modal_code = '''      {/* ENLARGED PHOTO EVIDENCE MODAL */}
      {enlargedImage && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1300,
            padding: '1.5rem'
          }}
          onClick={() => setEnlargedImage(null)}
        >
          <div style={{ position: 'relative', maxWidth: '90vw', maxHeight: '90vh' }} onClick={e => e.stopPropagation()}>
            <button
              onClick={() => setEnlargedImage(null)}
              style={{
                position: 'absolute',
                top: '-40px',
                right: '0',
                background: 'none',
                border: 'none',
                color: '#fff',
                fontSize: '1.5rem',
                cursor: 'pointer'
              }}
            >
              <X size={28} />
            </button>
            <img 
              src={enlargedImage} 
              alt="Enlarged Evidence" 
              style={{ maxWidth: '100%', maxHeight: '85vh', borderRadius: '8px', objectFit: 'contain', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }} 
            />
          </div>
        </div>
      )}
    </div>
  );
}'''

content = content.replace('    </div>\n  );\n}', enlarged_modal_code, 1)

with open('frontend/src/pages/CentreDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Modal evidence patch completed successfully!")
