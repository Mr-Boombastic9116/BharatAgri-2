import React, { useState, useEffect } from 'react';
import {
  Users, UserPlus, Calendar, Package, DollarSign, MessageSquare,
  ShieldCheck, Search, CheckCircle, AlertCircle, FileText, ArrowRight
} from 'lucide-react';
import {
  getAssignedFarmers, registerFarmerByAgent, bookSlot, getCentres,
  getSlots, createComplaint, getComplaints
} from '../services/api';
import { useTranslation } from '../context/LanguageContext';

export default function AgentDashboard({ user, navigate }) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('farmers');
  const [loading, setLoading] = useState(true);
  const [farmers, setFarmers] = useState([]);
  const [centres, setCentres] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Register farmer form
  const [farmerName, setFarmerName] = useState('');
  const [farmerMobile, setFarmerMobile] = useState('');
  const [farmerVillage, setFarmerVillage] = useState('Ponda');
  const [farmerAadhaar, setFarmerAadhaar] = useState('');
  const [farmerLandArea, setFarmerLandArea] = useState('2.5');
  const [farmerCrop, setFarmerCrop] = useState('Paddy');
  const [regMsg, setRegMsg] = useState(null);

  // Assist booking form
  const [selectedFarmerId, setSelectedFarmerId] = useState('');
  const [selectedCentreId, setSelectedCentreId] = useState('');
  const [bookingDate, setBookingDate] = useState('');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlotId, setSelectedSlotId] = useState('');
  const [bookQuantity, setBookQuantity] = useState('30');
  const [bookCrop, setBookCrop] = useState('Paddy');
  const [bookingMsg, setBookingMsg] = useState(null);

  // Complaint form
  const [complaintSubject, setComplaintSubject] = useState('');
  const [complaintDesc, setComplaintDesc] = useState('');
  const [complaintMsg, setComplaintMsg] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [farmersData, centresData, complaintsData] = await Promise.all([
        getAssignedFarmers(),
        getCentres(),
        getComplaints()
      ]);
      setFarmers(farmersData || []);
      setCentres(centresData || []);
      setComplaints(complaintsData || []);
      if (centresData && centresData.length > 0) {
        setSelectedCentreId(centresData[0].centre_id || centresData[0].id);
      }
      if (farmersData && farmersData.length > 0) {
        setSelectedFarmerId(farmersData[0].farmer_id || farmersData[0].id);
      }
    } catch (err) {
      console.error('Error loading agent data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRegisterFarmer = async (e) => {
    e.preventDefault();
    setRegMsg(null);
    try {
      const res = await registerFarmerByAgent({
        name: farmerName,
        mobile: farmerMobile,
        village: farmerVillage,
        aadhaar_hash: farmerAadhaar ? `AADHAAR-${farmerAadhaar.slice(-4)}` : 'AADHAAR-OK',
        land_area_hectares: parseFloat(farmerLandArea) || 2.5,
        primary_crop: farmerCrop
      });
      setRegMsg({ type: 'success', text: `Farmer ${farmerName} registered successfully! Assigned ID: ${res.farmer_id || 'OK'}` });
      setFarmerName('');
      setFarmerMobile('');
      loadData();
    } catch (err) {
      setRegMsg({ type: 'error', text: err.message || 'Farmer registration failed' });
    }
  };

  const handleFetchSlots = async (cId, d) => {
    if (!cId || !d) return;
    try {
      const res = await getSlots(cId, d);
      const slots = Array.isArray(res) ? res : (res.data || []);
      setAvailableSlots(slots);
      if (slots.length > 0) setSelectedSlotId(slots[0].id);
    } catch (err) {
      console.error('Error fetching slots:', err);
    }
  };

  const handleAssistBooking = async (e) => {
    e.preventDefault();
    setBookingMsg(null);
    if (!selectedSlotId) {
      setBookingMsg({ type: 'error', text: 'Please select an available slot.' });
      return;
    }
    try {
      const res = await bookSlot(
        selectedFarmerId,
        selectedCentreId,
        parseInt(selectedSlotId),
        bookCrop,
        parseFloat(bookQuantity)
      );
      setBookingMsg({ type: 'success', text: `Slot booked successfully for farmer! Appointment Code: ${res.appointment_id || res.id}` });
    } catch (err) {
      setBookingMsg({ type: 'error', text: err.message || 'Booking failed' });
    }
  };

  const handleFileComplaint = async (e) => {
    e.preventDefault();
    setComplaintMsg(null);
    try {
      await createComplaint({
        centre_id: selectedCentreId || 'CENTRE-GOA-01',
        category: 'Agent Assistance',
        priority: 'MEDIUM',
        subject: complaintSubject,
        description: complaintDesc
      });
      setComplaintMsg({ type: 'success', text: 'Grievance submitted successfully. Tracking ticket created.' });
      setComplaintSubject('');
      setComplaintDesc('');
      loadData();
    } catch (err) {
      setComplaintMsg({ type: 'error', text: err.message || 'Submission failed' });
    }
  };

  const filteredFarmers = farmers.filter((f) => {
    const q = searchQuery.toLowerCase();
    return (
      (f.name && f.name.toLowerCase().includes(q)) ||
      (f.farmer_id && f.farmer_id.toLowerCase().includes(q)) ||
      (f.village && f.village.toLowerCase().includes(q))
    );
  });

  return (
    <div className="agent-dashboard" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ backgroundColor: '#e0f2fe', color: '#0369a1', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase' }}>
              Village Cluster Portal
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
              Assigned Agent ID: {user?.user_id || 'agent@bharatagri.demo'}
            </span>
          </div>
          <h1 style={{ fontSize: '1.75rem', marginTop: '0.25rem', color: 'var(--secondary)' }}>
            Agricultural Extension & Village Agent Workspace
          </h1>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', borderBottom: '1px solid var(--border)', paddingBottom: '0.25rem' }}>
        {[
          { id: 'farmers', label: 'Assigned Farmers & e-KYC', icon: Users },
          { id: 'register', label: 'Register New Farmer', icon: UserPlus },
          { id: 'book', label: 'Assist Slot Booking', icon: Calendar },
          { id: 'complaints', label: 'Submit Complaint', icon: MessageSquare }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                padding: '0.6rem 1rem', border: 'none',
                borderBottom: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                backgroundColor: 'transparent',
                color: isActive ? 'var(--primary)' : 'var(--muted)',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.9rem', cursor: 'pointer', whiteSpace: 'nowrap'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: ASSIGNED FARMERS */}
      {activeTab === 'farmers' && (
        <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
            <h3 style={{ fontSize: '1.1rem', color: 'var(--secondary)' }}>
              Assigned Village Cultivators ({farmers.length} Registered)
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '0.4rem 0.75rem', backgroundColor: 'var(--bg-page)' }}>
              <Search size={16} color="var(--muted)" />
              <input
                type="text"
                placeholder="Search farmer or village..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '0.85rem', color: 'var(--secondary)' }}
              />
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left', color: 'var(--muted)' }}>
                  <th style={{ padding: '0.75rem' }}>Farmer ID</th>
                  <th style={{ padding: '0.75rem' }}>Name</th>
                  <th style={{ padding: '0.75rem' }}>Mobile</th>
                  <th style={{ padding: '0.75rem' }}>Village / District</th>
                  <th style={{ padding: '0.75rem' }}>Land Area</th>
                  <th style={{ padding: '0.75rem' }}>e-KYC Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredFarmers.slice(0, 15).map((f) => (
                  <tr key={f.id || f.farmer_id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{f.farmer_id || `FRM-${f.id}`}</td>
                    <td style={{ padding: '0.75rem' }}>{f.name}</td>
                    <td style={{ padding: '0.75rem' }}>{f.mobile}</td>
                    <td style={{ padding: '0.75rem' }}>{f.village || 'Ponda'} • {f.district || 'North Goa'}</td>
                    <td style={{ padding: '0.75rem' }}>{f.land_area_hectares || '2.5'} Ha</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span style={{
                        display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                        padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600,
                        backgroundColor: 'var(--success-bg)', color: 'var(--success-text)'
                      }}>
                        <CheckCircle size={12} />
                        VERIFIED
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: REGISTER FARMER */}
      {activeTab === 'register' && (
        <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', maxWidth: '650px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)' }}>
            Register New Farmer into BharatAgri
          </h3>

          {regMsg && (
            <div style={{
              padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem',
              backgroundColor: regMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
              color: regMsg.type === 'success' ? 'var(--success-text)' : 'var(--danger-text)'
            }}>
              {regMsg.text}
            </div>
          )}

          <form onSubmit={handleRegisterFarmer} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                Farmer Full Name *
              </label>
              <input
                type="text"
                required
                value={farmerName}
                onChange={(e) => setFarmerName(e.target.value)}
                placeholder="e.g. Ramesh V. Naik"
                style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Mobile Number *
                </label>
                <input
                  type="tel"
                  required
                  value={farmerMobile}
                  onChange={(e) => setFarmerMobile(e.target.value)}
                  placeholder="10-digit mobile"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Village / Locality *
                </label>
                <input
                  type="text"
                  required
                  value={farmerVillage}
                  onChange={(e) => setFarmerVillage(e.target.value)}
                  placeholder="e.g. Ponda North"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Cultivated Land Area (Hectares)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={farmerLandArea}
                  onChange={(e) => setFarmerLandArea(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Primary Crop
                </label>
                <select
                  value={farmerCrop}
                  onChange={(e) => setFarmerCrop(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                >
                  <option value="Paddy">Paddy</option>
                  <option value="Wheat">Wheat</option>
                  <option value="Maize">Maize</option>
                  <option value="Cotton">Cotton</option>
                  <option value="Soybean">Soybean</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                Aadhaar Last 4 Digits (e-KYC)
              </label>
              <input
                type="text"
                maxLength={4}
                value={farmerAadhaar}
                onChange={(e) => setFarmerAadhaar(e.target.value)}
                placeholder="e.g. 8492"
                style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <button
              type="submit"
              style={{
                marginTop: '0.5rem', padding: '0.75rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary)', color: '#ffffff', border: 'none',
                fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer'
              }}
            >
              Verify & Register Farmer
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: ASSIST SLOT BOOKING */}
      {activeTab === 'book' && (
        <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', maxWidth: '650px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)' }}>
            Assisted Slot Booking for Assigned Farmer
          </h3>

          {bookingMsg && (
            <div style={{
              padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem',
              backgroundColor: bookingMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
              color: bookingMsg.type === 'success' ? 'var(--success-text)' : 'var(--danger-text)'
            }}>
              {bookingMsg.text}
            </div>
          )}

          <form onSubmit={handleAssistBooking} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                Select Farmer *
              </label>
              <select
                value={selectedFarmerId}
                onChange={(e) => setSelectedFarmerId(e.target.value)}
                style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              >
                {farmers.map((f) => (
                  <option key={f.id || f.farmer_id} value={f.farmer_id || f.id}>
                    {f.name} ({f.farmer_id || `FRM-${f.id}`}) - {f.village}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Target Centre *
                </label>
                <select
                  value={selectedCentreId}
                  onChange={(e) => {
                    setSelectedCentreId(e.target.value);
                    if (bookingDate) handleFetchSlots(e.target.value, bookingDate);
                  }}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                >
                  {centres.map((c) => (
                    <option key={c.centre_id || c.id} value={c.centre_id || c.id}>
                      {c.centre_name} ({c.district})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Appointment Date *
                </label>
                <input
                  type="date"
                  required
                  value={bookingDate}
                  onChange={(e) => {
                    setBookingDate(e.target.value);
                    handleFetchSlots(selectedCentreId, e.target.value);
                  }}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                Select Time Slot *
              </label>
              {availableSlots.length > 0 ? (
                <select
                  value={selectedSlotId}
                  onChange={(e) => setSelectedSlotId(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                >
                  {availableSlots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.start_time} - {s.end_time} (Cap: {s.max_capacity}Q)
                    </option>
                  ))}
                </select>
              ) : (
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)', padding: '0.5rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                  {bookingDate ? 'No active slots for this date. (Centre may be non-operational or slots unconfigured)' : 'Select appointment date to view available time slots.'}
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Crop Type
                </label>
                <select
                  value={bookCrop}
                  onChange={(e) => setBookCrop(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                >
                  <option value="Paddy">Paddy</option>
                  <option value="Wheat">Wheat</option>
                  <option value="Maize">Maize</option>
                  <option value="Cotton">Cotton</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Estimated Quantity (Quintals)
                </label>
                <input
                  type="number"
                  required
                  value={bookQuantity}
                  onChange={(e) => setBookQuantity(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>
            </div>

            <button
              type="submit"
              style={{
                marginTop: '0.5rem', padding: '0.75rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary)', color: '#ffffff', border: 'none',
                fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer'
              }}
            >
              Confirm Appointment & Generate QR
            </button>
          </form>
        </div>
      )}

      {/* TAB 4: COMPLAINTS */}
      {activeTab === 'complaints' && (
        <div style={{ background: 'var(--bg-card)', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', maxWidth: '650px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)' }}>
            Submit Operational Grievance
          </h3>

          {complaintMsg && (
            <div style={{
              padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem',
              backgroundColor: complaintMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
              color: complaintMsg.type === 'success' ? 'var(--success-text)' : 'var(--danger-text)'
            }}>
              {complaintMsg.text}
            </div>
          )}

          <form onSubmit={handleFileComplaint} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                Subject / Title *
              </label>
              <input
                type="text"
                required
                value={complaintSubject}
                onChange={(e) => setComplaintSubject(e.target.value)}
                placeholder="e.g. Weighbridge delay or moisture tester variance"
                style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                Description & Impact *
              </label>
              <textarea
                required
                rows={4}
                value={complaintDesc}
                onChange={(e) => setComplaintDesc(e.target.value)}
                placeholder="Provide specific details, truck numbers, or affected farmer IDs..."
                style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <button
              type="submit"
              style={{
                marginTop: '0.5rem', padding: '0.75rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary)', color: '#ffffff', border: 'none',
                fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer'
              }}
            >
              Submit Grievance to Control Room
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
