import React, { useEffect, useState } from 'react';
import {
  getFarmerBookings, getFarmerProfile, getTraceabilityLot, createComplaint, getComplaints,
  getFarmerCrops, addFarmerCrop, updateFarmerCrop, deleteFarmerCrop, updateFarmerProfile,
  getBookingWorkflowStatus, getFarmerMarketIntelligence, getFarmerDailyIntelligence
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import AppointmentCard from '../components/AppointmentCard';
import {
  Calendar, PlusCircle, User, Hash, Clock, QrCode, X, Phone, MapPin,
  Package, DollarSign, MessageSquare, ShieldCheck, CheckCircle, FileText,
  Edit, Trash2, Plus, Save, TrendingUp, AlertTriangle, Layers, Activity, ArrowRight, Sparkles
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';
import { useTranslation } from '../context/LanguageContext';

export default function FarmerDashboard({ user, navigate }) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('overview');
  const [bookings, setBookings] = useState([]);
  const [farmerProfile, setFarmerProfile] = useState(null);
  const [crops, setCrops] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  // QR Pass Modal state
  const [selectedPassBooking, setSelectedPassBooking] = useState(null);

  // Traceability Modal state
  const [traceModalLot, setTraceModalLot] = useState(null);
  const [traceLoading, setTraceLoading] = useState(false);

  // Complaint Form
  const [compSubject, setCompSubject] = useState('');
  const [compCategory, setCompCategory] = useState('Weighment Discrepancy');
  const [compDesc, setCompDesc] = useState('');
  const [compMsg, setCompMsg] = useState(null);

  // Profile editing
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({});
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState(null);

  // Crop CRUD
  const [showAddCrop, setShowAddCrop] = useState(false);
  const [cropForm, setCropForm] = useState({ crop_name: '', season: 'Kharif 2026-27', sowing_date: '', expected_harvest_date: '', estimated_quantity_quintals: '' });
  const [editingCropId, setEditingCropId] = useState(null);
  const [cropMsg, setCropMsg] = useState(null);
  const [cropSaving, setCropSaving] = useState(false);

  // Intelligence & Live Workflow Tracker State
  const [dailyIntel, setDailyIntel] = useState(null);
  const [marketIntel, setMarketIntel] = useState(null);
  const [marketIntelLoading, setMarketIntelLoading] = useState(false);
  const [workflowData, setWorkflowData] = useState(null);
  const [workflowLoading, setWorkflowLoading] = useState(false);
  const [selectedWorkflowBooking, setSelectedWorkflowBooking] = useState(null);

  const farmerIdentifier = user?.user_id;

  const loadWorkflowStatus = (bId) => {
    if (!bId) return;
    setWorkflowLoading(true);
    getBookingWorkflowStatus(bId)
      .then(data => setWorkflowData(data))
      .catch(err => console.error('Error loading workflow status:', err))
      .finally(() => setWorkflowLoading(false));
  };

  useEffect(() => {
    if (user && user.user_id) {
      Promise.all([
        getFarmerBookings(user.user_id),
        getFarmerProfile(user.user_id).catch(() => null),
        getComplaints().catch(() => []),
        getFarmerCrops(user.user_id).catch(() => []),
        getFarmerDailyIntelligence(user.user_id).catch(() => null)
      ])
        .then(([bData, pData, cData, cropsData, dailyData]) => {
          setBookings(bData || []);
          setFarmerProfile(pData);
          setComplaints(cData || []);
          setCrops(cropsData || (pData?.crops || []));
          setDailyIntel(dailyData);

          // If there is an active booking, load its live 8-step workflow
          const activeB = (bData || []).find(b => !['CANCELLED', 'REJECTED', 'EXPIRED'].includes(b.status));
          if (activeB) {
            setSelectedWorkflowBooking(activeB);
            loadWorkflowStatus(activeB.appointment_id || activeB.id);
          }

          if (pData) {
            setProfileForm({
              name: pData.name || '',
              mobile: pData.mobile || '',
              email: pData.email || '',
              address: pData.address || '',
              village: pData.village || '',
              taluka: pData.taluka || '',
              district: pData.district || '',
              state: pData.state || '',
              land_area_hectares: pData.land_area_hectares || '',
              bank_name: pData.bank_name || '',
              bank_account_no: pData.bank_account_no || '',
              bank_ifsc: pData.bank_ifsc || ''
            });
          }
        })
        .catch((err) => console.error('Error loading farmer data:', err))
        .finally(() => setLoading(false));
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === 'intelligence' && user?.user_id && !marketIntel) {
      setMarketIntelLoading(true);
      getFarmerMarketIntelligence(user.user_id)
        .then(data => setMarketIntel(data))
        .catch(err => console.error('Error fetching market intelligence:', err))
        .finally(() => setMarketIntelLoading(false));
    }
  }, [activeTab, user, marketIntel]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      const updated = await updateFarmerProfile(farmerIdentifier, profileForm);
      setFarmerProfile(prev => ({ ...prev, ...updated }));
      setProfileMsg({ type: 'success', text: 'Profile updated successfully.' });
      setEditingProfile(false);
    } catch (err) {
      setProfileMsg({ type: 'error', text: err.message || 'Profile update failed' });
    } finally {
      setProfileSaving(false);
    }
  };

  const handleAddCrop = async (e) => {
    e.preventDefault();
    setCropSaving(true);
    setCropMsg(null);
    try {
      const payload = {
        ...cropForm,
        estimated_quantity_quintals: parseFloat(cropForm.estimated_quantity_quintals),
        sowing_date: cropForm.sowing_date || null,
        expected_harvest_date: cropForm.expected_harvest_date || null
      };
      if (editingCropId) {
        const updated = await updateFarmerCrop(farmerIdentifier, editingCropId, payload);
        setCrops(prev => prev.map(c => c.id === editingCropId ? updated : c));
        setCropMsg({ type: 'success', text: `Crop '${updated.crop_name}' updated.` });
        setEditingCropId(null);
      } else {
        const newCrop = await addFarmerCrop(farmerIdentifier, payload);
        setCrops(prev => [...prev, newCrop]);
        setCropMsg({ type: 'success', text: `Crop '${newCrop.crop_name}' added.` });
      }
      setShowAddCrop(false);
      setCropForm({ crop_name: '', season: 'Kharif 2026-27', sowing_date: '', expected_harvest_date: '', estimated_quantity_quintals: '' });
    } catch (err) {
      setCropMsg({ type: 'error', text: err.message || 'Failed to save crop' });
    } finally {
      setCropSaving(false);
    }
  };

  const handleDeleteCrop = async (cropId, cropName) => {
    if (!window.confirm(`Remove crop '${cropName}' from your profile?`)) return;
    try {
      await deleteFarmerCrop(farmerIdentifier, cropId);
      setCrops(prev => prev.filter(c => c.id !== cropId));
      setCropMsg({ type: 'success', text: `Crop '${cropName}' removed.` });
    } catch (err) {
      setCropMsg({ type: 'error', text: err.message });
    }
  };

  const handleEditCrop = (crop) => {
    setEditingCropId(crop.id);
    setCropForm({
      crop_name: crop.crop_name,
      season: crop.season || 'Kharif 2026-27',
      sowing_date: crop.sowing_date ? crop.sowing_date.split('T')[0] : '',
      expected_harvest_date: crop.expected_harvest_date ? crop.expected_harvest_date.split('T')[0] : '',
      estimated_quantity_quintals: crop.estimated_quantity_quintals || ''
    });
    setShowAddCrop(true);
  };

  const handleViewTraceability = async (bookingIdOrLot) => {
    try {
      setTraceLoading(true);
      const data = await getTraceabilityLot(bookingIdOrLot);
      setTraceModalLot(data);
    } catch (err) {
      alert('Traceability lot details: ' + (err.message || 'Not yet generated'));
    } finally {
      setTraceLoading(false);
    }
  };

  const handleFileComplaint = async (e) => {
    e.preventDefault();
    setCompMsg(null);
    try {
      await createComplaint({
        centre_id: farmerProfile?.preferred_centre || 'CENTRE-GOA-01',
        category: compCategory,
        priority: 'MEDIUM',
        subject: compSubject,
        description: compDesc
      });
      setCompMsg({ type: 'success', text: 'Complaint submitted successfully! Control room alerted.' });
      setCompSubject('');
      setCompDesc('');
      const updated = await getComplaints();
      setComplaints(updated || []);
    } catch (err) {
      setCompMsg({ type: 'error', text: err.message || 'Failed to submit complaint' });
    }
  };

  const upcomingBooking = bookings.find(
    (b) => b.status === 'CONFIRMED' || b.status === 'BOOKED' || b.status === 'ARRIVED' || b.status === 'Confirmed'
  );

  return (
    <div className="farmer-dashboard" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', color: 'var(--secondary)' }}>
            Welcome, {user.name}
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
            Kisan Portal • Direct MSP Procurement & DBT Settlement Tracker
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => navigate('book-slot')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.6rem 1.25rem' }}
        >
          <PlusCircle size={18} /> {t('book_slot')}
        </button>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', borderBottom: '1px solid var(--border)', paddingBottom: '0.25rem' }}>
        {[
          { id: 'overview', label: 'Dashboard & Appointments', icon: Calendar },
          { id: 'intelligence', label: 'Market Intelligence & Insights', icon: TrendingUp },
          { id: 'profile', label: 'Profile & My Crops', icon: User },
          { id: 'procurement', label: 'Procurement & Lots', icon: Package },
          { id: 'payments', label: 'DBT Payments', icon: DollarSign },
          { id: 'complaints', label: 'Grievance / Help', icon: MessageSquare }
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

      {/* TAB 1: OVERVIEW & BOOKINGS */}
      {activeTab === 'overview' && (
        <>
          {/* DAILY INTELLIGENCE BANNER */}
          {dailyIntel && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(59, 130, 246, 0.08) 100%)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '1.25rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.85rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Sparkles size={20} color="var(--primary)" />
                  <span style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--secondary)' }}>
                    Kisan Daily Intelligence Summary • {dailyIntel.date}
                  </span>
                </div>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.6rem', borderRadius: '12px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)' }}>
                  State: {farmerProfile?.state || 'Goa'}
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '0.75rem', fontSize: '0.85rem' }}>
                {dailyIntel.active_appointment ? (
                  <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>APPOINTMENT STATUS</span>
                    <strong style={{ color: 'var(--primary)' }}>{dailyIntel.active_appointment.crop} ({dailyIntel.active_appointment.quantity_quintals} Q)</strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--secondary)', marginTop: '0.2rem' }}>
                      Status: <span style={{ fontWeight: 700 }}>{dailyIntel.active_appointment.status}</span> • Slot: {dailyIntel.active_appointment.slot_date}
                    </div>
                  </div>
                ) : (
                  <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>APPOINTMENT STATUS</span>
                    <span style={{ color: 'var(--muted)' }}>No active booking. Slots available at nearby centres.</span>
                  </div>
                )}

                {dailyIntel.crop_demand_alerts?.length > 0 && (
                  <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>DEMAND OPPORTUNITY</span>
                    <strong style={{ color: 'var(--secondary)' }}>{dailyIntel.crop_demand_alerts[0].crop}</strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                      {dailyIntel.crop_demand_alerts[0].message}
                    </div>
                  </div>
                )}

                {dailyIntel.price_intelligence_alerts?.length > 0 && (
                  <div style={{ backgroundColor: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 600 }}>PRICE INTELLIGENCE ADVISORY</span>
                    <strong style={{ color: 'var(--success)' }}>
                      {dailyIntel.price_intelligence_alerts[0].crop} • AI Est: ₹{dailyIntel.price_intelligence_alerts[0].ai_estimated_price}/Q
                    </strong>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                      {dailyIntel.price_intelligence_alerts[0].advisory}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Quick Info Badges */}
          <div className="card" style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <User size={22} />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>CULTIVATOR</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--secondary)' }}>{user.name}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '50%', backgroundColor: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Hash size={22} />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>FARMER CODE</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--secondary)' }}>{farmerProfile?.farmer_code || user.user_id}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '50%', backgroundColor: 'var(--success-bg)', color: 'var(--success-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ShieldCheck size={22} />
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>e-KYC & AADHAAR</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--success)' }}>VERIFIED (DBT Active)</div>
              </div>
            </div>
          </div>

          {/* LIVE 8-STEP PROCUREMENT LIFECYCLE WORKFLOW TRACKER */}
          {workflowData && (
            <div className="card" style={{ padding: '1.5rem', border: '1px solid var(--primary-border)', backgroundColor: 'var(--bg-card)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <Activity size={20} color="var(--primary)" />
                    <h3 style={{ fontSize: '1.15rem', color: 'var(--secondary)', margin: 0, fontWeight: 800 }}>
                      Live Intake & Procurement Lifecycle Tracker
                    </h3>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '0.25rem 0 0 0' }}>
                    Appointment: <strong style={{ color: 'var(--primary)' }}>{workflowData.appointment_id}</strong> ({workflowData.crop} • {workflowData.booked_quantity} Qtl at {workflowData.centre_name})
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    padding: '0.4rem 0.85rem', borderRadius: '16px',
                    backgroundColor: 'var(--primary-light)', color: 'var(--primary)',
                    fontWeight: 800, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem'
                  }}>
                    <span>Current Process:</span>
                    <span style={{ textDecoration: 'underline' }}>{workflowData.current_process_name}</span>
                  </div>
                  <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                    {workflowData.completed_count} of 8 Steps Complete ({workflowData.progress_percentage}%)
                  </span>
                </div>
              </div>

              {/* Progress Line */}
              <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--border)', borderRadius: '3px', marginBottom: '1.5rem', overflow: 'hidden' }}>
                <div style={{ width: `${workflowData.progress_percentage}%`, height: '100%', backgroundColor: 'var(--primary)', transition: 'width 0.4s ease' }} />
              </div>

              {/* 8 Step Nodes */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.6rem', marginBottom: '1.25rem' }}>
                {workflowData.steps.map((step) => {
                  const isDone = step.completed;
                  const isCurrent = !isDone && (workflowData.steps.find(s => !s.completed)?.step_id === step.step_id);

                  return (
                    <div
                      key={step.step_id}
                      style={{
                        padding: '0.75rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        textAlign: 'center',
                        backgroundColor: isDone ? 'rgba(16, 185, 129, 0.08)' : (isCurrent ? 'rgba(59, 130, 246, 0.12)' : 'var(--bg-page)'),
                        border: isDone ? '1px solid rgba(16, 185, 129, 0.4)' : (isCurrent ? '2px solid var(--primary)' : '1px solid var(--border)')
                      }}
                    >
                      <div style={{
                        width: '28px', height: '28px', borderRadius: '50%',
                        margin: '0 auto 0.4rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        backgroundColor: isDone ? 'var(--primary)' : (isCurrent ? '#3b82f6' : 'var(--border)'),
                        color: '#ffffff', fontSize: '0.75rem', fontWeight: 800
                      }}>
                        {isDone ? '✓' : step.step_number}
                      </div>
                      <div style={{ fontSize: '0.8rem', fontWeight: 700, color: isDone ? 'var(--primary)' : (isCurrent ? '#1d4ed8' : 'var(--muted)') }}>
                        {step.step_name}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--muted)', marginTop: '0.2rem' }}>
                        {step.timestamp ? step.timestamp.split(' ')[1] || step.timestamp : (isCurrent ? 'In Progress' : 'Pending')}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Verified Metrics Chips */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.85rem', paddingTop: '0.85rem', borderTop: '1px solid var(--border)', fontSize: '0.85rem' }}>
                {workflowData.actual_quantity_received && (
                  <div style={{ padding: '0.35rem 0.75rem', borderRadius: '4px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)' }}>Actual Weighed: </span>
                    <strong style={{ color: 'var(--secondary)' }}>{workflowData.actual_quantity_received} Qtl</strong>
                  </div>
                )}
                {workflowData.quality_result && (
                  <div style={{ padding: '0.35rem 0.75rem', borderRadius: '4px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)' }}>Quality Grade: </span>
                    <strong style={{ color: 'var(--primary)' }}>{workflowData.quality_result.quality_grade} (Moisture: {workflowData.quality_result.moisture_content_pct}%)</strong>
                  </div>
                )}
                {workflowData.payment_status && (
                  <div style={{ padding: '0.35rem 0.75rem', borderRadius: '4px', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--muted)' }}>DBT Payment: </span>
                    <strong style={{ color: 'var(--success)' }}>{workflowData.payment_status.status} (₹{workflowData.payment_status.amount_inr?.toLocaleString()})</strong>
                  </div>
                )}
                {workflowData.relevant_timestamp && (
                  <div style={{ marginLeft: 'auto', color: 'var(--muted)', fontSize: '0.8rem', alignSelf: 'center' }}>
                    Last Process Activity: {workflowData.relevant_timestamp}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Grid: Upcoming Appointment & Quick Action */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {/* UPCOMING APPOINTMENT CARD */}
            <div className="card">
              <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Calendar size={20} color="var(--primary)" /> UPCOMING APPOINTMENT
                </h3>
                {upcomingBooking && <StatusBadge status={upcomingBooking.status} />}
              </div>

              {upcomingBooking ? (
                <div style={{ backgroundColor: 'var(--primary-light)', borderRadius: 'var(--radius-md)', padding: '1.25rem', border: '1px solid var(--primary-border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                    <span style={{ fontWeight: 800, color: 'var(--primary)', fontSize: '1.1rem' }}>
                      {upcomingBooking.appointment_id || upcomingBooking.booking_id}
                    </span>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--muted)' }}>{upcomingBooking.crop}</span>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem 0.5rem', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                    <div>
                      <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 700 }}>CENTRE</span>
                      <strong style={{ color: 'var(--secondary)' }}>{upcomingBooking.centre_name || upcomingBooking.centre_id}</strong>
                    </div>

                    <div>
                      <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 700 }}>QUANTITY</span>
                      <strong style={{ color: 'var(--secondary)' }}>{upcomingBooking.quantity} Quintals</strong>
                    </div>

                    <div>
                      <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 700 }}>DATE</span>
                      <strong style={{ color: 'var(--secondary)' }}>{formatDateDisplay(upcomingBooking.date)}</strong>
                    </div>

                    <div>
                      <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem', fontWeight: 700 }}>TIME SLOT</span>
                      <strong style={{ color: 'var(--secondary)' }}>{upcomingBooking.time_slot}</strong>
                    </div>
                  </div>

                  <button
                    className="btn btn-primary btn-sm"
                    style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
                    onClick={() => setSelectedPassBooking(upcomingBooking)}
                  >
                    <QrCode size={16} /> VIEW QR PROCUREMENT PASS
                  </button>
                </div>
              ) : (
                <div style={{ padding: '2rem 1rem', textAlign: 'center', color: 'var(--muted)' }}>
                  <p>No pending upcoming procurement appointment found.</p>
                </div>
              )}
            </div>

            {/* QUICK ACTION CTA */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '2rem' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <PlusCircle size={28} />
              </div>
              <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: 'var(--secondary)' }}>Schedule Next Delivery</h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '1.25rem' }}>
                Reserve your verified electronic gate slot at an operational MSP centre to eliminate queues.
              </p>
              <button
                className="btn btn-primary"
                onClick={() => navigate('book-slot')}
                style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
              >
                <PlusCircle size={18} /> Book Procurement Slot
              </button>
            </div>
          </div>

          {/* ALL BOOKINGS TABLE */}
          <div className="card">
            <div className="card-header" style={{ marginBottom: '1rem' }}>
              <h3 className="card-title">Procurement Appointments History</h3>
            </div>

            {loading ? (
              <p style={{ padding: '1rem' }}>Loading appointments...</p>
            ) : bookings.length === 0 ? (
              <p style={{ padding: '1rem', color: 'var(--muted)' }}>No previous appointments recorded.</p>
            ) : (
              <div className="table-container" style={{ overflowX: 'auto' }}>
                <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left', color: 'var(--muted)' }}>
                      <th style={{ padding: '0.75rem' }}>Appointment Code</th>
                      <th style={{ padding: '0.75rem' }}>Centre</th>
                      <th style={{ padding: '0.75rem' }}>Crop</th>
                      <th style={{ padding: '0.75rem' }}>Quantity</th>
                      <th style={{ padding: '0.75rem' }}>Date</th>
                      <th style={{ padding: '0.75rem' }}>Status</th>
                      <th style={{ padding: '0.75rem' }}>Pass</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map((b) => (
                      <tr key={b.id || b.appointment_id} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '0.75rem', fontWeight: 600, color: 'var(--primary)' }}>
                          {b.appointment_id || b.booking_id}
                        </td>
                        <td style={{ padding: '0.75rem' }}>{b.centre_name || b.centre_id}</td>
                        <td style={{ padding: '0.75rem' }}>{b.crop}</td>
                        <td style={{ padding: '0.75rem' }}>{b.quantity} Q</td>
                        <td style={{ padding: '0.75rem' }}>{formatDateDisplay(b.date)}</td>
                        <td style={{ padding: '0.75rem' }}><StatusBadge status={b.status} /></td>
                        <td style={{ padding: '0.75rem' }}>
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => setSelectedPassBooking(b)}
                            style={{ padding: '3px 8px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                          >
                            <QrCode size={12} /> QR Pass
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* TAB 2: PROFILE & MY CROPS */}
      {activeTab === 'profile' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Profile Info & Edit Form */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <User size={18} color="var(--primary)" /> Cultivator Profile & Land Holdings
              </h3>
              <button
                onClick={() => { setEditingProfile(!editingProfile); setProfileMsg(null); }}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.45rem 0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
              >
                <Edit size={14} /> {editingProfile ? 'Cancel Edit' : 'Edit Profile'}
              </button>
            </div>

            {profileMsg && (
              <div style={{ padding: '0.65rem 0.85rem', marginBottom: '0.85rem', borderRadius: 'var(--radius-sm)', backgroundColor: profileMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)', color: profileMsg.type === 'success' ? 'var(--success-text)' : 'var(--danger-text)', fontSize: '0.875rem' }}>
                {profileMsg.text}
              </div>
            )}

            {editingProfile ? (
              <form onSubmit={handleSaveProfile} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.85rem' }}>
                {[['Name', 'name', 'text'], ['Mobile', 'mobile', 'text'], ['Email', 'email', 'email'], ['Village', 'village', 'text'], ['Taluka', 'taluka', 'text'], ['District', 'district', 'text'], ['State', 'state', 'text'], ['Land Area (Ha)', 'land_area_hectares', 'number'], ['Bank Name', 'bank_name', 'text'], ['Account No', 'bank_account_no', 'text'], ['IFSC Code', 'bank_ifsc', 'text']].map(([label, field, type]) => (
                  <div key={field}>
                    <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--secondary)', display: 'block', marginBottom: '0.25rem' }}>{label}</label>
                    <input
                      type={type}
                      value={profileForm[field] || ''}
                      onChange={e => setProfileForm(p => ({ ...p, [field]: e.target.value }))}
                      style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', fontSize: '0.875rem' }}
                    />
                  </div>
                ))}
                <div style={{ gridColumn: '1 / -1', display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <button type="submit" disabled={profileSaving} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 1.25rem', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '0.875rem', opacity: profileSaving ? 0.65 : 1 }}>
                    <Save size={14} /> {profileSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.9rem' }}>
                {[
                  ['Farmer ID / Code', farmerProfile?.farmer_code || user.farmer_code || user.user_id],
                  ['User ID / Login Code', farmerProfile?.user_id || user.user_id],
                  ['Registered Name', farmerProfile?.name || user.name],
                  ['Mobile Number', farmerProfile?.mobile || user.mobile || '—'],
                  ['Email', farmerProfile?.email || '—'],
                  ['Date of Birth', farmerProfile?.dob || '—'],
                  ['Village / Taluka', `${farmerProfile?.village || '—'} / ${farmerProfile?.taluka || '—'}`],
                  ['District / State', `${farmerProfile?.district || '—'}, ${farmerProfile?.state || '—'}`],
                  ['Cultivated Land Area', `${farmerProfile?.land_area_hectares || '—'} Hectares`],
                  ['e-KYC Status', farmerProfile?.ekyc_status || 'VERIFIED'],
                  ['DBT Bank Account', farmerProfile?.bank_name ? (
                    `${farmerProfile.bank_name} — ` +
                    (farmerProfile.bank_account_no && farmerProfile.bank_account_no.length > 4
                      ? '*'.repeat(farmerProfile.bank_account_no.length - 4) + farmerProfile.bank_account_no.slice(-4)
                      : farmerProfile.bank_account_no || 'N/A') +
                    ` (IFSC: ${farmerProfile.bank_ifsc || 'N/A'})`
                  ) : 'Not configured']
                ].map(([label, value]) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
                    <span style={{ color: 'var(--muted)' }}>{label}:</span>
                    <strong style={{ color: 'var(--secondary)', textAlign: 'right', maxWidth: '60%' }}>{value}</strong>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Crops Section */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Package size={18} color="#0284c7" /> My Crops & Harvest Estimates
              </h3>
              <button
                onClick={() => { setShowAddCrop(!showAddCrop); setEditingCropId(null); setCropForm({ crop_name: '', season: 'Kharif 2026-27', sowing_date: '', expected_harvest_date: '', estimated_quantity_quintals: '' }); }}
                style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.45rem 0.9rem', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}
              >
                <Plus size={14} /> {showAddCrop ? 'Cancel' : 'Add Crop'}
              </button>
            </div>

            {cropMsg && (
              <div style={{ padding: '0.65rem 0.85rem', marginBottom: '0.85rem', borderRadius: 'var(--radius-sm)', backgroundColor: cropMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)', color: cropMsg.type === 'success' ? 'var(--success-text)' : 'var(--danger-text)', fontSize: '0.875rem' }}>
                {cropMsg.text}
              </div>
            )}

            {showAddCrop && (
              <form onSubmit={handleAddCrop} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '1.25rem', padding: '1rem', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--secondary)', display: 'block', marginBottom: '0.25rem' }}>Crop Name *</label>
                  <select value={cropForm.crop_name} onChange={e => setCropForm(p => ({ ...p, crop_name: e.target.value }))} required style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }}>
                    <option value="">Select crop</option>
                    {['Paddy', 'Wheat', 'Maize', 'Soybean', 'Cotton', 'Jowar', 'Bajra', 'Gram', 'Tur', 'Groundnut', 'Sunflower', 'Sugarcane'].map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--secondary)', display: 'block', marginBottom: '0.25rem' }}>Season</label>
                  <select value={cropForm.season} onChange={e => setCropForm(p => ({ ...p, season: e.target.value }))} style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }}>
                    {['Kharif 2026-27', 'Rabi 2026-27', 'Zaid 2027', 'Kharif 2025-26', 'Rabi 2025-26'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--secondary)', display: 'block', marginBottom: '0.25rem' }}>Sowing Date</label>
                  <input type="date" value={cropForm.sowing_date} onChange={e => setCropForm(p => ({ ...p, sowing_date: e.target.value }))} style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--secondary)', display: 'block', marginBottom: '0.25rem' }}>Expected Harvest</label>
                  <input type="date" value={cropForm.expected_harvest_date} onChange={e => setCropForm(p => ({ ...p, expected_harvest_date: e.target.value }))} style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--secondary)', display: 'block', marginBottom: '0.25rem' }}>Estimated Qty (Quintals) *</label>
                  <input type="number" min={0.1} step={0.1} required value={cropForm.estimated_quantity_quintals} onChange={e => setCropForm(p => ({ ...p, estimated_quantity_quintals: e.target.value }))} style={{ width: '100%', padding: '0.55rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }} />
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.5rem' }}>
                  <button type="submit" disabled={cropSaving} style={{ flex: 1, padding: '0.55rem', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--primary)', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', fontSize: '0.875rem', opacity: cropSaving ? 0.65 : 1 }}>
                    {cropSaving ? 'Saving...' : (editingCropId ? 'Update Crop' : 'Add Crop')}
                  </button>
                </div>
              </form>
            )}

            {crops.length === 0 ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--muted)' }}>
                <Package size={36} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
                <p>No crops registered yet. Click "Add Crop" to register your harvest.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {crops.map((crop) => (
                  <div key={crop.id} style={{ padding: '0.85rem 1rem', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.3rem' }}>
                        <strong style={{ fontSize: '1rem', color: 'var(--secondary)' }}>{crop.crop_name}</strong>
                        <span style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.72rem', fontWeight: 700, backgroundColor: 'var(--success-bg)', color: 'var(--success-text)' }}>MSP ELIGIBLE</span>
                      </div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--muted)', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
                        <span>Season: <strong style={{ color: 'var(--secondary)' }}>{crop.season}</strong></span>
                        <span>Estimated: <strong style={{ color: 'var(--primary)' }}>{crop.estimated_quantity_quintals} Q</strong></span>
                        {crop.sowing_date && <span>Sown: {crop.sowing_date}</span>}
                        {crop.expected_harvest_date && <span>Harvest: {crop.expected_harvest_date}</span>}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button onClick={() => handleEditCrop(crop)} style={{ padding: '0.35rem 0.65rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}><Edit size={12} /> Edit</button>
                      <button onClick={() => handleDeleteCrop(crop.id, crop.crop_name)} style={{ padding: '0.35rem 0.65rem', borderRadius: '4px', border: '1px solid var(--danger)', backgroundColor: 'var(--danger-bg)', color: 'var(--danger-text)', cursor: 'pointer', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}><Trash2 size={12} /> Remove</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: PROCUREMENT & LOT TRACEABILITY */}
      {activeTab === 'procurement' && (
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Package size={18} color="var(--primary)" /> Procurement Records & End-to-End Lot Traceability
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '1.25rem' }}>
            Every grain delivered at a BharatAgri procurement yard receives a unique cryptographic Lot ID mapping collection, laboratory moisture checks, digital scale weighment, and storage stack.
          </p>

          <div className="table-container" style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left', color: 'var(--muted)' }}>
                  <th style={{ padding: '0.75rem' }}>Booking Code</th>
                  <th style={{ padding: '0.75rem' }}>Crop</th>
                  <th style={{ padding: '0.75rem' }}>Yard Centre</th>
                  <th style={{ padding: '0.75rem' }}>Procurement Status</th>
                  <th style={{ padding: '0.75rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id || b.appointment_id} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{b.appointment_id || b.booking_id}</td>
                    <td style={{ padding: '0.75rem' }}>{b.crop}</td>
                    <td style={{ padding: '0.75rem' }}>{b.centre_name || b.centre_id}</td>
                    <td style={{ padding: '0.75rem' }}><StatusBadge status={b.status} /></td>
                    <td style={{ padding: '0.75rem' }}>
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={() => handleViewTraceability(b.appointment_id || b.id)}
                        style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                      >
                        Inspect Lot & Quality
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: DBT PAYMENTS */}
      {activeTab === 'payments' && (
        <div className="card">
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DollarSign size={18} color="#16a34a" /> Direct Benefit Transfer (DBT) Payouts
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left', color: 'var(--muted)' }}>
                  <th style={{ padding: '0.75rem' }}>Transaction Ref</th>
                  <th style={{ padding: '0.75rem' }}>Crop</th>
                  <th style={{ padding: '0.75rem' }}>Procured Qty</th>
                  <th style={{ padding: '0.75rem' }}>MSP Rate</th>
                  <th style={{ padding: '0.75rem' }}>Gross DBT Amount</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {bookings.filter((b) => ['PROCURED', 'PAID', 'Procured'].includes(b.status)).map((b, idx) => {
                  const qty = parseFloat(b.quantity) || 25;
                  const msp = 2300;
                  const total = qty * msp;
                  return (
                    <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 600 }}>UTR202688192{idx}</td>
                      <td style={{ padding: '0.75rem' }}>{b.crop}</td>
                      <td style={{ padding: '0.75rem' }}>{qty} Quintals</td>
                      <td style={{ padding: '0.75rem' }}>₹ {msp.toLocaleString()} / Q</td>
                      <td style={{ padding: '0.75rem', fontWeight: 700, color: 'var(--primary)' }}>
                        ₹ {total.toLocaleString()}
                      </td>
                      <td style={{ padding: '0.75rem' }}>
                        <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, backgroundColor: 'var(--success-bg)', color: 'var(--success-text)' }}>
                          SETTLED (DBT)
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: GRIEVANCES */}
      {activeTab === 'complaints' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.5rem' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)' }}>
              File a Grievance with Control Room
            </h3>

            {compMsg && (
              <div style={{
                padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem',
                backgroundColor: compMsg.type === 'success' ? 'var(--success-bg)' : 'var(--danger-bg)',
                color: compMsg.type === 'success' ? 'var(--success-text)' : 'var(--danger-text)'
              }}>
                {compMsg.text}
              </div>
            )}

            <form onSubmit={handleFileComplaint} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Category *
                </label>
                <select
                  value={compCategory}
                  onChange={(e) => setCompCategory(e.target.value)}
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                >
                  <option value="Weighment Discrepancy">Weighment Discrepancy</option>
                  <option value="Quality Inspection Delay">Quality Inspection Delay</option>
                  <option value="DBT Payment Delay">DBT Payment Delay</option>
                  <option value="Bardan Shortage">Bardan Shortage</option>
                  <option value="Gate Gatekeeper Verification">Gatekeeper Verification</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Subject *
                </label>
                <input
                  type="text"
                  required
                  value={compSubject}
                  onChange={(e) => setCompSubject(e.target.value)}
                  placeholder="e.g. Weighbridge delay or moisture variance"
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Details *
                </label>
                <textarea
                  required
                  rows={4}
                  value={compDesc}
                  onChange={(e) => setCompDesc(e.target.value)}
                  placeholder="Describe your issue with exact centre name and booking code..."
                  style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>

              <button
                type="submit"
                style={{
                  padding: '0.75rem', borderRadius: 'var(--radius-sm)',
                  backgroundColor: 'var(--primary)', color: '#ffffff', border: 'none',
                  fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer'
                }}
              >
                Submit Grievance
              </button>
            </form>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--secondary)' }}>
              Recent Filed Tickets ({complaints.length})
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {complaints.map((c) => (
                <div key={c.id} style={{ padding: '0.85rem', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong style={{ fontSize: '0.9rem', color: 'var(--secondary)' }}>{c.subject}</strong>
                    <span style={{ padding: '0.15rem 0.5rem', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 700, backgroundColor: c.status === 'RESOLVED' ? 'var(--success-bg)' : '#fef3c7', color: c.status === 'RESOLVED' ? 'var(--success-text)' : '#92400e' }}>
                      {c.status}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.3rem' }}>{c.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 6: MARKET INTELLIGENCE & INSIGHTS */}
      {activeTab === 'intelligence' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Advisory Notice Header */}
          <div style={{
            padding: '1.25rem',
            backgroundColor: 'rgba(59, 130, 246, 0.08)',
            border: '1px solid rgba(59, 130, 246, 0.25)',
            borderRadius: 'var(--radius-md)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.35rem' }}>
              <TrendingUp size={20} color="var(--primary)" />
              <h2 style={{ fontSize: '1.25rem', color: 'var(--secondary)', margin: 0, fontWeight: 800 }}>
                Kisan Market Intelligence & Commodity Price Trends
              </h2>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: 0 }}>
              Regional economic analytics for <strong>{farmerProfile?.state || 'Goa'}</strong> based on government procurement volumes,
              current buffer targets, and official MSP price benchmarks.
            </p>
            <div style={{
              marginTop: '0.75rem', padding: '0.6rem 0.85rem',
              backgroundColor: 'var(--bg-card)', borderRadius: '4px',
              borderLeft: '4px solid var(--primary)', fontSize: '0.8rem', color: 'var(--muted)'
            }}>
              ⚖️ <strong>Official Advisory Disclaimer:</strong> All procurement estimates represent machine learning projections grounded in historical intake, supply-demand balances, and statutory MSP minimum rate guarantees. No future personal income or speculative price guarantees are implied.
            </div>
          </div>

          {marketIntelLoading ? (
            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted)' }}>
              Loading real-time market intelligence & model projections...
            </div>
          ) : marketIntel ? (
            <>
              {/* SECTION A & B: DEMAND TRENDS & SUPPLY DEFICITS */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem' }}>
                {/* HIGH DEMAND CROPS */}
                <div className="card">
                  <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TrendingUp size={20} color="var(--primary)" />
                    <h3 className="card-title">High Demand Commodities in State</h3>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '1rem' }}>
                    Crops currently experiencing elevated procurement velocity and strategic buffer restocking.
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {marketIntel.high_demand_crops?.map((c, i) => (
                      <div key={i} style={{ padding: '0.85rem', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong style={{ fontSize: '0.95rem', color: 'var(--secondary)' }}>{c.crop_name}</strong>
                          <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, backgroundColor: 'var(--primary-light)', color: 'var(--primary)' }}>
                            Demand: {c.demand_level}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--muted)', marginTop: '0.4rem' }}>
                          <span>Season: {c.season} • Trend: <strong style={{ color: 'var(--success)' }}>{c.demand_trend}</strong></span>
                          <span>Official MSP: <strong>₹{c.official_msp}/Q</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* SUPPLY DEFICIT & SHORTAGES */}
                <div className="card">
                  <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertTriangle size={20} color="#eab308" />
                    <h3 className="card-title">State Supply Deficit Forecast</h3>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '1rem' }}>
                    Commodities where active procurement intake remains below the state's seasonal reserve quota.
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {marketIntel.supply_shortages?.length > 0 ? (
                      marketIntel.supply_shortages.map((s, i) => (
                        <div key={i} style={{ padding: '0.85rem', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <strong style={{ fontSize: '0.95rem', color: 'var(--secondary)' }}>{s.crop_name}</strong>
                            <span style={{ padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, backgroundColor: '#fef3c7', color: '#92400e' }}>
                              Deficit: {s.projected_deficit_quintals.toLocaleString()} Q
                            </span>
                          </div>
                          <p style={{ fontSize: '0.8rem', color: 'var(--muted)', margin: '0.4rem 0 0 0' }}>{s.reason}</p>
                        </div>
                      ))
                    ) : (
                      <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--muted)', fontSize: '0.85rem' }}>
                        Adequate seasonal buffer reserves maintained across state centres.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* SECTION C: PRICE OPPORTUNITIES (STRICT NON-GUARANTEE ADVISORY) */}
              <div className="card">
                <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={20} color="var(--primary)" />
                  <h3 className="card-title">Estimated Procurement Price Indicators (AI XGBoost Model)</h3>
                </div>
                <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '1rem' }}>
                  Dynamic model evaluation respecting <code>FINAL ESTIMATED PRICE = MAX(AI ESTIMATE, OFFICIAL MSP)</code>.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                  {marketIntel.price_opportunities?.map((p, i) => (
                    <div key={i} style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--bg-page)', border: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <strong style={{ fontSize: '1rem', color: 'var(--secondary)' }}>{p.crop_name}</strong>
                        <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: '4px', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', fontWeight: 700 }}>
                          {p.season}
                        </span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem', fontSize: '0.85rem' }}>
                        <div>
                          <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>OFFICIAL MSP</span>
                          <strong style={{ color: 'var(--secondary)' }}>₹{p.official_msp}/Q</strong>
                        </div>
                        <div>
                          <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>AI ESTIMATED RATE</span>
                          <strong style={{ color: 'var(--primary)' }}>₹{p.ai_estimated_procurement_price}/Q</strong>
                        </div>
                      </div>

                      <div style={{ padding: '0.6rem', borderRadius: '4px', backgroundColor: 'var(--bg-card)', border: '1px solid var(--border)', fontSize: '0.8rem', color: 'var(--secondary)', lineHeight: 1.4 }}>
                        💬 <em>"{p.advisory_note}"</em>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* SECTION D: FARMER-SPECIFIC CROPS COMPARATIVE ANALYSIS */}
              <div className="card">
                <div className="card-header" style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Package size={20} color="var(--primary)" />
                    <h3 className="card-title">My Registered Crops • Market Condition Benchmark</h3>
                  </div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 800, color: 'var(--primary)' }}>
                    Portfolio Est. Total: ₹{marketIntel.total_estimated_portfolio_value?.toLocaleString()}
                  </div>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '2px solid var(--border)', color: 'var(--muted)' }}>
                        <th style={{ padding: '0.75rem 0.5rem' }}>CROP</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>QUANTITY</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>OFFICIAL MSP</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>AI ESTIMATED PRICE</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>EST. TOTAL VALUE</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>DEMAND LEVEL</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>PERISHABILITY</th>
                        <th style={{ padding: '0.75rem 0.5rem' }}>MARKET ADVISORY</th>
                      </tr>
                    </thead>
                    <tbody>
                      {marketIntel.my_crops_intelligence?.map((c, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                          <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: 'var(--secondary)' }}>{c.crop_name}</td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>{c.registered_quantity_quintals} Q</td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>₹{c.official_msp_rate}/Q</td>
                          <td style={{ padding: '0.75rem 0.5rem', fontWeight: 700, color: 'var(--primary)' }}>₹{c.ai_estimated_procurement_price}/Q</td>
                          <td style={{ padding: '0.75rem 0.5rem', fontWeight: 800, color: 'var(--success)' }}>₹{c.estimated_total_value?.toLocaleString()}</td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>
                            <span style={{ padding: '0.2rem 0.4rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 700, backgroundColor: c.demand_level === 'HIGH' ? 'var(--primary-light)' : 'var(--bg-page)', color: c.demand_level === 'HIGH' ? 'var(--primary)' : 'var(--muted)' }}>
                              {c.demand_level}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem' }}>
                            <span style={{
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              color: (c.is_perishable || c.perishability === 'HIGH' || c.perishability === 'CRITICAL' || c.perishability === 'MEDIUM') ? '#dc2626' : 'var(--muted)'
                            }}>
                              {(c.is_perishable || c.perishability === 'HIGH' || c.perishability === 'CRITICAL' || c.perishability === 'MEDIUM')
                                ? `Perishable (${c.shelf_life || (c.approx_shelf_life_days ? `${c.approx_shelf_life_days}d` : '2-3 Days')})`
                                : 'Not applicable'}
                            </span>
                          </td>
                          <td style={{ padding: '0.75rem 0.5rem', fontSize: '0.8rem', color: 'var(--secondary)' }}>
                            {c.market_condition_summary}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>
              Market intelligence data unavailable for current region.
            </div>
          )}
        </div>
      )}

      {/* QR PASS MODAL */}
      {selectedPassBooking && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '580px' }}>
            <button
              onClick={() => setSelectedPassBooking(null)}
              style={{
                position: 'absolute', top: '12px', right: '12px', zIndex: 10,
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: '50%', width: '32px', height: '32px',
                display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
              }}
            >
              <X size={18} />
            </button>
            <AppointmentCard booking={selectedPassBooking} />
          </div>
        </div>
      )}

      {/* LOT TRACEABILITY MODAL */}
      {traceModalLot && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '640px', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius-md)', padding: '1.5rem', border: '1px solid var(--border)', maxHeight: '90vh', overflowY: 'auto' }}>
            <button
              onClick={() => setTraceModalLot(null)}
              style={{
                position: 'absolute', top: '12px', right: '12px',
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: '50%', width: '32px', height: '32px',
                display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
              }}
            >
              <X size={18} />
            </button>

            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.25rem', color: 'var(--secondary)' }}>
              Procurement Lot Traceability Passport
            </h3>
            <span style={{ fontSize: '0.85rem', color: 'var(--primary)', fontWeight: 700 }}>
              {traceModalLot.lot_id}
            </span>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1.25rem', fontSize: '0.85rem' }}>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>CROP & QUANTITY</span>
                <strong>{traceModalLot.crop} • {traceModalLot.quantity_quintals} Q</strong>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>QUALITY GRADE</span>
                <strong style={{ color: 'var(--primary)' }}>{traceModalLot.quality?.grade || 'Grade A'} (Moisture: {traceModalLot.quality?.moisture_content_pct}%)</strong>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>WEIGHMENT NET</span>
                <strong>{traceModalLot.weighment?.net_weight || traceModalLot.quantity_quintals} Quintals</strong>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>STORAGE LOCATION</span>
                <strong>{traceModalLot.warehouse_name || 'Warehouse Stack A-04'}</strong>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>TOTAL SETTLEMENT</span>
                <strong style={{ color: 'var(--primary)' }}>₹ {traceModalLot.procurement?.total_value?.toLocaleString() || '57,500'}</strong>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-page)', borderRadius: '4px' }}>
                <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>DBT STATUS</span>
                <strong style={{ color: 'var(--success)' }}>{traceModalLot.payment?.status || 'PAID'}</strong>
              </div>
            </div>

            {/* Complete Traceability History / Lifecycle Timeline */}
            {traceModalLot.lifecycle_stages && traceModalLot.lifecycle_stages.length > 0 && (
              <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border)', paddingTop: '1.25rem' }}>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '0.85rem' }}>
                  End-to-End Procurement Lifecycle History
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {traceModalLot.lifecycle_stages.map((stage, idx) => (
                    <div key={idx} style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.85rem',
                      padding: '0.65rem 0.85rem',
                      backgroundColor: stage.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.06)' : 'var(--bg-page)',
                      borderRadius: '6px',
                      borderLeft: `4px solid ${stage.status === 'COMPLETED' ? '#10B981' : (stage.status === 'IN_PROGRESS' ? '#F59E0B' : '#94A3B8')}`
                    }}>
                      <div style={{
                        width: '24px', height: '24px', borderRadius: '50%',
                        backgroundColor: stage.status === 'COMPLETED' ? '#10B981' : (stage.status === 'IN_PROGRESS' ? '#F59E0B' : '#CBD5E1'),
                        color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '0.75rem', fontWeight: 700, flexShrink: 0
                      }}>
                        {stage.stage_number}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-main)' }}>
                            {stage.stage_name}
                          </span>
                          <span style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            backgroundColor: stage.status === 'COMPLETED' ? '#DCFCE7' : (stage.status === 'IN_PROGRESS' ? '#FEF3C7' : '#F1F5F9'),
                            color: stage.status === 'COMPLETED' ? '#166534' : (stage.status === 'IN_PROGRESS' ? '#92400E' : '#475569')
                          }}>
                            {stage.status}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Ref: <strong style={{ color: 'var(--text-main)' }}>{stage.reference}</strong> • Date: {stage.date}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
                          {stage.details}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
