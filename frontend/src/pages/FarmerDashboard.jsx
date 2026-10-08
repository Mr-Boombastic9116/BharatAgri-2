import React, { useEffect, useState, useCallback } from 'react';
import {
  getFarmerBookings, getFarmerProfile, getTraceabilityLot, createComplaint, getComplaints,
  getFarmerCrops, addFarmerCrop, updateFarmerCrop, deleteFarmerCrop, updateFarmerProfile,
  getFarmerOverview, getLiveQueue, trackToken, recommendCentre, getRecommendedSlots,
  getCropsMaster, getFarmerNotifications, getEstimatedPrice
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import AppointmentCard from '../components/AppointmentCard';
import {
  Calendar, Ticket, Users, IndianRupee, MapPin, Phone,
  Sparkles, Bell, HelpCircle, ArrowRight, RefreshCw, CheckCircle2,
  AlertCircle, Clock, QrCode, X, FileText, ChevronRight, Scale,
  ShieldCheck, AlertTriangle, TrendingUp, Info, User, ExternalLink,
  Layers, Compass, Home
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';
import { useTranslation } from '../context/LanguageContext';

export default function FarmerDashboard({ user, navigate }) {
  const { t } = useTranslation();
  const farmerIdentifier = user?.user_id;

  // Primary navigation: 'main' is simple low-literacy dashboard; advanced tabs are secondary
  const [activeTab, setActiveTab] = useState('main'); // 'main' | 'msp_prices' | 'ai_insights' | 'alerts' | 'centres' | 'crops'

  // Core Data
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [overviewData, setOverviewData] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [farmerProfile, setFarmerProfile] = useState(null);
  const [cropsMaster, setCropsMaster] = useState([]);
  const [crops, setCrops] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [complaints, setComplaints] = useState([]);

  // Live Queue & Token Tracking
  const [liveQueueData, setLiveQueueData] = useState(null);
  const [selectedCentreId, setSelectedCentreId] = useState('C001');
  const [queueRefreshing, setQueueRefreshing] = useState(false);

  // Recommendations
  const [nearbyCentres, setNearbyCentres] = useState([]);

  // Modals for the 6 Main Action Cards
  const [activeModal, setActiveModal] = useState(null); // 'queue', 'payment', 'centres', 'help'
  const [selectedPassBooking, setSelectedPassBooking] = useState(null);

  // Complaint Form
  const [compSubject, setCompSubject] = useState('');
  const [compCategory, setCompCategory] = useState('Weighment Discrepancy');
  const [compDesc, setCompDesc] = useState('');
  const [compMsg, setCompMsg] = useState(null);

  // Interactive MSP & Estimated Price Calculator State
  const [calcCrop, setCalcCrop] = useState('Paddy');
  const [calcQuantity, setCalcQuantity] = useState('42');
  const [calcPriceInfo, setCalcPriceInfo] = useState(null);
  const [loadingCalcPrice, setLoadingCalcPrice] = useState(false);

  // Load Overview Data
  const loadDashboardData = useCallback(() => {
    if (!farmerIdentifier) return;
    setLoading(true);
    Promise.all([
      getFarmerOverview(farmerIdentifier).catch(() => null),
      getFarmerBookings(farmerIdentifier).catch(() => []),
      getFarmerProfile(farmerIdentifier).catch(() => null),
      getCropsMaster().catch(() => ({ crops: [] })),
      getFarmerNotifications(farmerIdentifier).catch(() => []),
      getComplaints().catch(() => []),
      getFarmerCrops(farmerIdentifier).catch(() => [])
    ])
      .then(([overview, bData, profile, cMasterRes, notifs, comps, fCrops]) => {
        setOverviewData(overview);
        setBookings(Array.isArray(bData) ? bData : []);
        setFarmerProfile(profile);
        setCropsMaster(cMasterRes?.crops || []);
        setNotifications(Array.isArray(notifs) ? notifs : []);
        setComplaints(Array.isArray(comps) ? comps : []);
        setCrops(fCrops || (profile?.crops || []));

        const activeCentre = overview?.token_tracking?.centre_id || bData?.[0]?.centre_id || 'C001';
        setSelectedCentreId(activeCentre);
        fetchLiveQueue(activeCentre);

        // Fetch nearby centres for farmer district
        recommendCentre({
          crop: 'Paddy',
          quantity: 40,
          farmer_id: farmerIdentifier,
          district: profile?.district || 'Pune'
        })
          .then(res => setNearbyCentres(res.centres || []))
          .catch(() => {});
      })
      .catch(err => console.error('Error loading farmer dashboard:', err))
      .finally(() => setLoading(false));
  }, [farmerIdentifier]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Fetch Live Queue
  const fetchLiveQueue = (centreId) => {
    setQueueRefreshing(true);
    getLiveQueue(centreId)
      .then(data => setLiveQueueData(data?.data || data))
      .catch(err => console.error('Error fetching live queue:', err))
      .finally(() => setQueueRefreshing(false));
  };

  // Fetch MSP price estimate for calculator
  useEffect(() => {
    if (calcCrop) {
      setLoadingCalcPrice(true);
      const qVal = parseFloat(calcQuantity) > 0 ? parseFloat(calcQuantity) : 42;
      getEstimatedPrice({
        crop: calcCrop,
        quantity: qVal,
        centre_id: selectedCentreId
      })
        .then(data => setCalcPriceInfo(data))
        .catch(() => setCalcPriceInfo(null))
        .finally(() => setLoadingCalcPrice(false));
    }
  }, [calcCrop, calcQuantity, selectedCentreId]);

  const handleFileComplaint = async (e) => {
    e.preventDefault();
    setCompMsg(null);
    try {
      await createComplaint({
        centre_id: selectedCentreId,
        category: compCategory,
        priority: 'MEDIUM',
        subject: compSubject,
        description: compDesc
      });
      setCompMsg({ type: 'success', text: 'Sahayata grievance submitted. A mandi officer will follow up.' });
      setCompSubject('');
      setCompDesc('');
      const updated = await getComplaints();
      setComplaints(updated || []);
    } catch (err) {
      setCompMsg({ type: 'error', text: err.message || 'Submission failed' });
    }
  };

  // Resolve Active Booking
  const activeBooking = bookings.find(b => !['COMPLETED', 'CANCELLED', 'REJECTED', 'EXPIRED'].includes(b.status)) || bookings[0] || null;
  const tokenData = overviewData?.token_tracking;
  const paymentSummary = overviewData?.payment_summary;

  // Active Token & Queue Numbers
  const userToken = tokenData?.token_number || activeBooking?.token || activeBooking?.token_number || (activeBooking ? `A${(activeBooking.id || 184) % 900 + 100}` : null);
  const farmersAhead = tokenData?.farmers_ahead ?? activeBooking?.farmers_ahead ?? liveQueueData?.waiting_count ?? 0;
  const waitMin = Math.round(tokenData?.estimated_waiting_time_minutes ?? activeBooking?.estimated_wait_min ?? liveQueueData?.estimated_wait_min ?? 15);
  const currentServingToken = liveQueueData?.currently_serving_token ?? (userToken ? `A${Math.max(1, (parseInt(String(userToken).replace(/\D/g, '')) || 184) - farmersAhead)}` : 'A177');
  const centreStatus = liveQueueData?.status_label || liveQueueData?.centre_status || 'Centre operating normally';
  const comeNowActive = tokenData?.come_now_alert || (userToken && farmersAhead <= 5 && activeBooking?.status !== 'COMPLETED');

  // Selected crop for display
  const primaryCrop = activeBooking?.crop || (crops[0]?.crop_name) || 'Paddy';

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '3rem' }}>

      {/* TOP HEADER: Simple & Clean (Rural Friendly) */}
      <div style={{
        backgroundColor: 'var(--surface)',
        borderRadius: '12px',
        padding: '1.25rem 1.75rem',
        border: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        boxShadow: '0 1px 4px rgba(0,0,0,0.04)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            backgroundColor: 'rgba(27, 77, 62, 0.1)',
            color: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <User size={28} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
              Namaste, {user?.name || farmerProfile?.name || 'Kisan Bhai'}
            </h1>
            <p style={{ margin: '2px 0 0 0', fontSize: '0.85rem', color: 'var(--muted)' }}>
              {farmerProfile?.village ? `${farmerProfile.village}, ` : ''}{farmerProfile?.district || 'Agricultural Zone'} • Farmer ID: {farmerProfile?.farmer_code || user?.user_id}
            </p>
          </div>
        </div>

        {/* TOP TAB SWITCHER: Main (Simple) vs Advanced Features */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => setActiveTab('main')}
            style={{
              padding: '0.55rem 1.1rem',
              borderRadius: '20px',
              border: activeTab === 'main' ? '2px solid var(--primary)' : '1px solid #cbd5e1',
              backgroundColor: activeTab === 'main' ? 'var(--primary)' : '#ffffff',
              color: activeTab === 'main' ? '#ffffff' : 'var(--secondary)',
              fontWeight: 800,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Home size={16} /> Home
          </button>

          <button
            onClick={() => setActiveTab('msp_prices')}
            style={{
              padding: '0.55rem 1.1rem',
              borderRadius: '20px',
              border: activeTab === 'msp_prices' ? '2px solid var(--primary)' : '1px solid #cbd5e1',
              backgroundColor: activeTab === 'msp_prices' ? 'var(--primary)' : '#ffffff',
              color: activeTab === 'msp_prices' ? '#ffffff' : 'var(--secondary)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <IndianRupee size={16} /> MSP & Estimated Price
          </button>

          <button
            onClick={() => setActiveTab('ai_insights')}
            style={{
              padding: '0.55rem 1.1rem',
              borderRadius: '20px',
              border: activeTab === 'ai_insights' ? '2px solid var(--primary)' : '1px solid #cbd5e1',
              backgroundColor: activeTab === 'ai_insights' ? 'var(--primary)' : '#ffffff',
              color: activeTab === 'ai_insights' ? '#ffffff' : 'var(--secondary)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Sparkles size={16} /> AI Insights
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            style={{
              padding: '0.55rem 1.1rem',
              borderRadius: '20px',
              border: activeTab === 'alerts' ? '2px solid var(--primary)' : '1px solid #cbd5e1',
              backgroundColor: activeTab === 'alerts' ? 'var(--primary)' : '#ffffff',
              color: activeTab === 'alerts' ? '#ffffff' : 'var(--secondary)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Bell size={16} /> Alerts ({notifications.length})
          </button>

          <button
            onClick={() => setActiveTab('centres')}
            style={{
              padding: '0.55rem 1.1rem',
              borderRadius: '20px',
              border: activeTab === 'centres' ? '2px solid var(--primary)' : '1px solid #cbd5e1',
              backgroundColor: activeTab === 'centres' ? 'var(--primary)' : '#ffffff',
              color: activeTab === 'centres' ? '#ffffff' : 'var(--secondary)',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Compass size={16} /> Centre Intelligence
          </button>
        </div>
      </div>

      {/* ============================================================== */}
      {/* TAB 1: MAIN SIMPLE FARMER DASHBOARD (PRIMARY HIERARCHY) */}
      {/* ============================================================== */}
      {activeTab === 'main' && (
        <>
          {/* URGENT "COME NOW" ADVISORY BANNER (Requirement 9) */}
          {comeNowActive && (
            <div style={{
              backgroundColor: 'var(--danger-bg)',
              border: '2px solid var(--danger)',
              borderRadius: '12px',
              padding: '1.25rem 1.5rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '1rem',
              boxShadow: '0 4px 12px rgba(239, 68, 68, 0.12)'
            }}>
              <div style={{
                backgroundColor: 'var(--danger)',
                color: '#ffffff',
                padding: '0.5rem',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0
              }}>
                <Bell size={24} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{
                    backgroundColor: '#dc2626',
                    color: '#ffffff',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    textTransform: 'uppercase'
                  }}>
                    Priority Notice
                  </span>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#991b1b' }}>
                    Your Turn Is Approaching
                  </h3>
                </div>
                <p style={{ margin: '0.5rem 0 0 0', fontSize: '1.1rem', fontWeight: 700, color: '#7f1d1d', lineHeight: 1.4 }}>
                  Only {farmersAhead} {farmersAhead === 1 ? 'farmer' : 'farmers'} ahead of you.
                  Please proceed to {activeBooking?.centre_name || activeBooking?.centre_id || 'Procurement Centre'}.
                </p>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#b91c1c' }}>
                  Estimated waiting time is {waitMin} minutes. Move to the weighbridge gate with your vehicle.
                </p>
              </div>
            </div>
          )}

          {/* ACTIVE BOOKING / TOKEN SUMMARY BAR (If booking exists) */}
          {userToken && activeBooking && (
            <div style={{
              backgroundColor: 'var(--surface)',
              border: '2px solid var(--primary)',
              borderRadius: '12px',
              padding: '1.25rem 1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              boxShadow: '0 2px 8px rgba(0,0,0,0.04)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
                <div style={{
                  backgroundColor: 'rgba(27, 77, 62, 0.1)',
                  border: '2px solid var(--primary)',
                  borderRadius: '10px',
                  padding: '8px 16px',
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                    Your Token
                  </div>
                  <div style={{ fontSize: '1.75rem', fontWeight: 900, color: 'var(--primary)', lineHeight: 1.1 }}>
                    {userToken}
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)' }}>
                      {activeBooking.crop} — {activeBooking.quantity} Q
                    </span>
                    <StatusBadge status={activeBooking.status} />
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '2px' }}>
                    {activeBooking.centre_name || activeBooking.centre_id} • {formatDateDisplay(activeBooking.date)} ({activeBooking.time_slot || activeBooking.start_time})
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={() => navigate('my-booking')}
                  className="btn btn-primary"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 700 }}
                >
                  <Ticket size={16} /> Open My Booking
                </button>
                <button
                  onClick={() => setSelectedPassBooking(activeBooking)}
                  className="btn btn-outline"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <QrCode size={16} /> View Pass
                </button>
              </div>
            </div>
          )}

          {/* THE 6 PRIMARY ACTION CARDS (Clean, Large, Low-Literacy Friendly) */}
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '1rem' }}>
              Main Services
            </h2>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.25rem'
            }}>
              
              {/* CARD 1: BOOK PROCUREMENT */}
              <div 
                className="card"
                onClick={() => navigate('book-slot')}
                style={{
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  backgroundColor: 'var(--surface)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
                  transition: 'transform 0.15s ease, box-shadow 0.15s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '10px',
                    backgroundColor: 'rgba(27, 77, 62, 0.12)', color: 'var(--primary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Calendar size={26} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Book Slot <ChevronRight size={14} />
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                    Book Procurement
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                    Reserve your date, preferred centre, and get a confirmed queue token.
                  </p>
                </div>
              </div>

              {/* CARD 2: MY BOOKING / TOKEN */}
              <div 
                className="card"
                onClick={() => navigate('my-booking')}
                style={{
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  backgroundColor: 'var(--surface)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '10px',
                    backgroundColor: 'rgba(27, 77, 62, 0.12)', color: 'var(--primary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Ticket size={26} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    My Pass <ChevronRight size={14} />
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                    My Booking & Token
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                    {userToken ? `Active Token: ${userToken} • ${activeBooking?.crop || 'Harvest'}` : 'View your active appointment and pass QR code.'}
                  </p>
                </div>
              </div>

              {/* CARD 3: LIVE QUEUE */}
              <div 
                className="card"
                onClick={() => setActiveModal('queue')}
                style={{
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  backgroundColor: 'var(--surface)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '10px',
                    backgroundColor: 'rgba(22, 163, 74, 0.12)', color: '#16a34a',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Users size={26} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#16a34a', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Live Status <ChevronRight size={14} />
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                    Live Queue
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                    Serving {currentServingToken} • {farmersAhead} ahead • Est. wait ~{waitMin} mins.
                  </p>
                </div>
              </div>

              {/* CARD 4: PAYMENT STATUS */}
              <div 
                className="card"
                onClick={() => setActiveModal('payment')}
                style={{
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  backgroundColor: 'var(--surface)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '10px',
                    backgroundColor: 'rgba(217, 119, 6, 0.12)', color: '#d97706',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <IndianRupee size={26} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#d97706', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Payment Details <ChevronRight size={14} />
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                    Payment Status
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                    ₹{paymentSummary ? paymentSummary.paid_rs?.toLocaleString('en-IN') : '60,168'} Disbursed • Direct DBT Bank Credit.
                  </p>
                </div>
              </div>

              {/* CARD 5: NEARBY / RECOMMENDED CENTRE */}
              <div 
                className="card"
                onClick={() => setActiveModal('centres')}
                style={{
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  backgroundColor: 'var(--surface)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '10px',
                    backgroundColor: 'rgba(27, 77, 62, 0.12)', color: 'var(--primary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <MapPin size={26} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Check Centres <ChevronRight size={14} />
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                    Nearby Centres
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                    {nearbyCentres[0]?.centre_name || 'Pune Procurement Centre 1'} • Active Weighbridge.
                  </p>
                </div>
              </div>

              {/* CARD 6: HELP & HELPLINE */}
              <div 
                className="card"
                onClick={() => setActiveModal('help')}
                style={{
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  backgroundColor: 'var(--surface)',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{
                    width: '48px', height: '48px', borderRadius: '10px',
                    backgroundColor: 'rgba(220, 38, 38, 0.12)', color: '#dc2626',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Phone size={26} />
                  </div>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#dc2626', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    Call Support <ChevronRight size={14} />
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                    Kisan Sahayata / Help
                  </h3>
                  <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                    Toll-Free 1800-180-1551 • Lodge grievance or weighment dispute.
                  </p>
                </div>
              </div>

            </div>
          </div>
        </>
      )}

      {/* ============================================================== */}
      {/* TAB 2: MSP & ESTIMATED PRICE (REQUIREMENT 4) */}
      {/* ============================================================== */}
      {activeTab === 'msp_prices' && (
        <div className="card" style={{ padding: '2rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <IndianRupee size={22} style={{ color: 'var(--primary)' }} />
              Minimum Support Price (MSP) & Estimated Procurement Value
            </h2>
            <p style={{ fontSize: '0.9rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
              Official government benchmark rates and interactive harvest valuation calculator
            </p>
          </div>

          {/* Calculator Controls */}
          <div style={{
            backgroundColor: 'var(--bg-page)',
            padding: '1.5rem',
            borderRadius: '10px',
            border: '1px solid var(--border)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" style={{ fontWeight: 700 }}>Select Crop</label>
              <select
                className="form-control"
                value={calcCrop}
                onChange={(e) => setCalcCrop(e.target.value)}
                style={{ fontWeight: 600 }}
              >
                {cropsMaster.length > 0 ? (
                  cropsMaster.map(c => (
                    <option key={c.crop_id || c.crop_name} value={c.crop_name}>
                      {c.crop_name} ({c.season || 'Annual'}) — Official MSP: ₹{c.msp_per_quintal || c.msp}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="Paddy">Paddy (Kharif) — MSP: ₹2,369 / Q</option>
                    <option value="Wheat">Wheat (Rabi) — MSP: ₹2,275 / Q</option>
                    <option value="Cotton">Cotton (Kharif) — MSP: ₹7,121 / Q</option>
                    <option value="Soybean">Soybean (Kharif) — MSP: ₹4,892 / Q</option>
                    <option value="Maize">Maize (Kharif) — MSP: ₹2,225 / Q</option>
                    <option value="Mustard">Mustard (Rabi) — MSP: ₹5,650 / Q</option>
                  </>
                )}
              </select>
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" style={{ fontWeight: 700 }}>Expected Quantity (Quintals)</label>
              <input
                type="number"
                step="0.5"
                min="1"
                className="form-control"
                value={calcQuantity}
                onChange={(e) => setCalcQuantity(e.target.value)}
                style={{ fontWeight: 600 }}
              />
            </div>
          </div>

          {/* CLEAR DISTINCTION: MSP vs ESTIMATED VALUE (Requirement 4) */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1.25rem',
            marginBottom: '1.5rem'
          }}>
            
            {/* Box 1: Official MSP */}
            <div style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '1.5rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--muted)', textTransform: 'uppercase' }}>
                Official Government MSP
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '6px' }}>
                ₹{calcPriceInfo?.official_msp?.toLocaleString('en-IN') || (calcCrop === 'Paddy' ? '2,369' : '2,275')}
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--muted)' }}> / quintal</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '4px' }}>
                Legal minimum floor price for {calcCrop}
              </div>
            </div>

            {/* Box 2: Expected Quantity */}
            <div style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '1.5rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--muted)', textTransform: 'uppercase' }}>
                Expected Quantity
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '6px' }}>
                {calcQuantity || '42'}
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--muted)' }}> quintals</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '4px' }}>
                Registered harvest lot size
              </div>
            </div>

            {/* Box 3: Estimated Procurement Value */}
            <div style={{
              backgroundColor: 'rgba(27, 77, 62, 0.08)',
              border: '2px solid var(--primary)',
              borderRadius: '12px',
              padding: '1.5rem',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase' }}>
                Estimated Procurement Value
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 900, color: 'var(--primary)', marginTop: '6px' }}>
                ₹{((parseFloat(calcQuantity) || 42) * (calcPriceInfo?.official_msp || (calcCrop === 'Paddy' ? 2369 : 2275))).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </div>
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary)', marginTop: '4px' }}>
                Expected Quantity × Rate
              </div>
            </div>

          </div>

          {/* Quality Disclaimer Notice */}
          <div style={{
            backgroundColor: 'var(--warning-bg)',
            border: '1px solid var(--warning)',
            borderRadius: '8px',
            padding: '1rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px'
          }}>
            <Info size={20} style={{ color: 'var(--warning)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.88rem', color: 'var(--warning-text)', lineHeight: 1.5 }}>
              <strong>Notice on Actual Disbursement:</strong> The estimated value shown above represents an indicative total based on applicable rates (e.g. Paddy @ ₹2,369/Q for 42 quintals = ₹99,498). Actual final disbursement depends upon physical weighment verification and quality/moisture grading performed at the procurement centre during intake.
            </div>
          </div>

          {/* Quick Book Button from MSP */}
          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            <button
              onClick={() => navigate('book-slot')}
              className="btn btn-primary btn-lg"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Calendar size={18} /> Book Procurement Slot for {calcCrop}
            </button>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 3: ADVANCED AI INSIGHTS */}
      {/* ============================================================== */}
      {activeTab === 'ai_insights' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="card" style={{ padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={20} style={{ color: 'var(--primary)' }} />
              Procurement AI Intelligence & Market Forecasts
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
              <div style={{ backgroundColor: 'var(--bg-page)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.25rem' }}>
                  Queue Waiting Time Model
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)', lineHeight: 1.4 }}>
                  Trained on 18,000 SIH appointment records using Gradient Boosting. Predicts dynamic gate delay based on arrival rates, scale count, and truck unloading schedules.
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--bg-page)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.25rem' }}>
                  Congestion Prediction
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)', lineHeight: 1.4 }}>
                  Evaluates centre daily metrics to detect peak surge hours. Automatically routes farmers to alternative underutilized centres to prevent bottleneck queues.
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--bg-page)', padding: '1.25rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.25rem' }}>
                  Visual Quality & Ripeness AI (Mango)
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)', lineHeight: 1.4 }}>
                  Multi-fruit watershed distance transform isolates touching fruits and evaluates coloration, surface defects, and maturity grade directly at the gate.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 4: NOTIFICATIONS & ALERTS */}
      {/* ============================================================== */}
      {activeTab === 'alerts' && (
        <div className="card" style={{ padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.75rem', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bell size={20} style={{ color: 'var(--primary)' }} />
              Notifications & Dispatch Notices ({notifications.length})
            </h2>
          </div>

          {notifications.length === 0 ? (
            <p style={{ color: 'var(--muted)', textAlign: 'center', padding: '2rem 0' }}>
              No notifications on record.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {notifications.map((n, i) => (
                <div key={n.notification_id || i} style={{
                  backgroundColor: 'var(--bg-page)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  padding: '1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '1rem'
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span style={{
                        backgroundColor: n.type === 'COME_NOW' ? 'var(--danger-bg)' : 'var(--primary-light)',
                        color: n.type === 'COME_NOW' ? 'var(--danger)' : 'var(--primary)',
                        padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 800
                      }}>
                        {n.type || 'ADVISORY'}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{n.sent_at}</span>
                    </div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--secondary)', marginTop: '4px' }}>
                      {n.message}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 5: CENTRE INTELLIGENCE */}
      {/* ============================================================== */}
      {activeTab === 'centres' && (
        <div className="card" style={{ padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Compass size={20} style={{ color: 'var(--primary)' }} />
            Procurement Centre Network & Live Congestion
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            {nearbyCentres.map((c) => (
              <div key={c.centre_id} style={{
                backgroundColor: 'var(--bg-page)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '1rem'
              }}>
                <div style={{ fontWeight: 800, color: 'var(--secondary)', fontSize: '1.05rem' }}>
                  {c.centre_name}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '2px' }}>
                  {c.district}, {c.state} • Centre ID: {c.centre_id}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.85rem' }}>
                  <span>Waiting Time:</span>
                  <strong>~{c.estimated_wait_minutes || 20} mins</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Current Queue:</span>
                  <strong>{c.current_queue || 4} farmers</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 1: LIVE QUEUE STATUS */}
      {/* ============================================================== */}
      {activeModal === 'queue' && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                Live Centre Queue Status
              </h3>
              <button onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{
              backgroundColor: 'var(--bg-page)',
              border: '2px solid var(--primary)',
              borderRadius: '12px',
              padding: '1.25rem',
              textAlign: 'center',
              marginBottom: '1.25rem'
            }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                Currently Serving Token
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--primary)', lineHeight: 1.1, marginTop: '2px' }}>
                {currentServingToken}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '4px' }}>
                Status: <strong>{centreStatus}</strong>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{ backgroundColor: 'var(--surface-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700 }}>YOUR TOKEN</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '2px' }}>
                  {userToken || 'No Active Booking'}
                </div>
              </div>
              <div style={{ backgroundColor: 'var(--surface-secondary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700 }}>FARMERS AHEAD</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 900, color: farmersAhead <= 5 ? 'var(--danger)' : 'var(--secondary)', marginTop: '2px' }}>
                  {farmersAhead}
                </div>
              </div>
            </div>

            <button onClick={() => setActiveModal(null)} className="btn btn-outline" style={{ width: '100%' }}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 2: PAYMENT HISTORY */}
      {/* ============================================================== */}
      {activeModal === 'payment' && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '580px', width: '100%', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                Payment & Disbursement Status
              </h3>
              <button onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{
              backgroundColor: 'rgba(27, 77, 62, 0.08)',
              border: '1px solid var(--primary-border)',
              borderRadius: '10px',
              padding: '1rem 1.25rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.25rem'
            }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: 700 }}>TOTAL DISBURSED (DBT)</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 900, color: 'var(--primary)' }}>
                  ₹{paymentSummary?.paid_rs?.toLocaleString('en-IN') || '60,168'}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>PENDING</div>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--warning)' }}>
                  ₹{paymentSummary?.pending_rs?.toLocaleString('en-IN') || '0'}
                </div>
              </div>
            </div>

            <h4 style={{ fontSize: '1rem', fontWeight: 800, marginBottom: '0.5rem', color: 'var(--secondary)' }}>
              Recent Transactions ({paymentSummary?.recent_transactions?.length || 0})
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '240px', overflowY: 'auto' }}>
              {(paymentSummary?.recent_transactions || []).map((t, idx) => (
                <div key={t.procurement_id || idx} style={{
                  padding: '10px 12px',
                  backgroundColor: 'var(--bg-page)',
                  borderRadius: '6px',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{t.crop} — {t.quantity_quintals} Q</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{t.date} • ₹{t.rate_rs_per_quintal}/Q</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 800, color: 'var(--success)' }}>₹{t.gross_amount_rs?.toLocaleString('en-IN')}</div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)' }}>{t.payment_status}</div>
                  </div>
                </div>
              ))}
            </div>

            <button onClick={() => setActiveModal(null)} className="btn btn-outline" style={{ width: '100%', marginTop: '1.25rem' }}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 3: NEARBY CENTRES */}
      {/* ============================================================== */}
      {activeModal === 'centres' && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '580px', width: '100%', padding: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.3rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                Recommended Procurement Centres
              </h3>
              <button onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '360px', overflowY: 'auto' }}>
              {nearbyCentres.map((c) => (
                <div key={c.centre_id} style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-page)',
                  borderRadius: '8px',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--secondary)' }}>
                      {c.centre_name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                      {c.district}, {c.state} • Wait: ~{c.estimated_wait_minutes || 20}m • Queue: {c.current_queue || 4}
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setActiveModal(null);
                      navigate('book-slot');
                    }}
                    className="btn btn-primary btn-sm"
                    style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                  >
                    Book Here
                  </button>
                </div>
              ))}
            </div>

            <button onClick={() => setActiveModal(null)} className="btn btn-outline" style={{ width: '100%', marginTop: '1.25rem' }}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 4: HELP & KISAN SAHAYATA */}
      {/* ============================================================== */}
      {activeModal === 'help' && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000, padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '580px', width: '100%', padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                Kisan Sahayata Helpline & Support
              </h3>
              <button onClick={() => setActiveModal(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
              <div style={{
                padding: '1rem', backgroundColor: 'var(--info-bg)', borderRadius: '8px',
                border: '1px solid var(--info)', display: 'flex', alignItems: 'center', gap: '1rem'
              }}>
                <Phone size={28} style={{ color: 'var(--info)' }} />
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--info-text)', fontWeight: 700, textTransform: 'uppercase' }}>
                    National Kisan Call Centre (Toll-Free)
                  </div>
                  <strong style={{ fontSize: '1.25rem', color: 'var(--info-text)' }}>1800-180-1551</strong>
                  <div style={{ fontSize: '0.75rem', color: 'var(--info-text)' }}>Available 06:00 AM to 10:00 PM • Free call</div>
                </div>
              </div>
            </div>

            <h4 style={{ fontSize: '1rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: 'var(--secondary)' }}>
              Lodge a Mandi Grievance or Inquiry
            </h4>

            {compMsg && (
              <div style={{
                padding: '0.75rem', borderRadius: '6px', marginBottom: '0.75rem',
                backgroundColor: compMsg.type === 'success' ? '#dcfce7' : '#fee2e2',
                color: compMsg.type === 'success' ? '#166534' : '#991b1b', fontWeight: 700
              }}>
                {compMsg.text}
              </div>
            )}

            <form onSubmit={handleFileComplaint} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Issue Category
                </label>
                <select
                  value={compCategory}
                  onChange={(e) => setCompCategory(e.target.value)}
                  className="form-control"
                >
                  <option value="Weighment Discrepancy">Weighment Discrepancy</option>
                  <option value="Payment Delay">Payment / DBT Delay</option>
                  <option value="Queue Issue">Gate Queue Bypass</option>
                  <option value="Quality Grading">Moisture / Quality Grading</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Summary
                </label>
                <input
                  type="text"
                  placeholder="e.g. Weighbridge WB-01 weight reading"
                  value={compSubject}
                  onChange={(e) => setCompSubject(e.target.value)}
                  required
                  className="form-control"
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, marginBottom: '0.3rem' }}>
                  Details
                </label>
                <textarea
                  placeholder="Describe your issue..."
                  value={compDesc}
                  onChange={(e) => setCompDesc(e.target.value)}
                  rows="3"
                  required
                  className="form-control"
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ padding: '0.75rem', fontWeight: 800, marginTop: '0.25rem' }}>
                Submit Sahayata Request
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL 5: DIGITAL APPOINTMENT PASS */}
      {/* ============================================================== */}
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
                background: 'var(--surface)', border: '1px solid var(--border)',
                color: 'var(--text-primary)',
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

    </div>
  );
}
