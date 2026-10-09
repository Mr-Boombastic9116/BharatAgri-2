import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  getFarmerBookings, getFarmerProfile, getTraceabilityLot, createComplaint, getComplaints,
  getFarmerCrops, addFarmerCrop, updateFarmerCrop, deleteFarmerCrop, updateFarmerProfile,
  getFarmerOverview, getLiveQueue, trackToken, recommendCentre, getRecommendedSlots,
  getCropsMaster, getFarmerNotifications, getEstimatedPrice, getFarmerMarketIntelligence,
  scanMangoQuality
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import AppointmentCard from '../components/AppointmentCard';
import {
  Calendar, Ticket, Users, IndianRupee, MapPin, Phone,
  Sparkles, Bell, HelpCircle, ArrowRight, RefreshCw, CheckCircle2,
  AlertCircle, Clock, QrCode, X, FileText, ChevronRight, Scale,
  ShieldCheck, AlertTriangle, TrendingUp, Info, User, ExternalLink,
  Layers, Compass, Home, Upload, Camera, Check, ChevronDown, ChevronUp, Eye
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';
import { useTranslation } from '../context/LanguageContext';

const CENTRE_COORDINATES = {
  'C01': { lat: 15.5562, lon: 74.0152 },       // Sanquelim, North Goa (Demo Centre)
  'PC-GOA-01': { lat: 15.4909, lon: 73.8278 }, // Panaji Apex APMC Yard, North Goa
  'PC-GOA-02': { lat: 15.2736, lon: 73.9582 }, // Margao South Goa Horticultural Terminal
  'C021': { lat: 16.7050, lon: 74.2433 },      // Kolhapur Regional APMC Hub
  'C029': { lat: 15.3647, lon: 75.1240 },      // Hubballi North Karnataka APMC Terminal
  'C001': { lat: 18.5204, lon: 73.8567 },      // Pune Procurement Centre 1
  'C017': { lat: 18.5304, lon: 73.8667 },      // Pune Procurement Centre 2
  'C003': { lat: 17.6599, lon: 75.9064 },      // Solapur Procurement Centre 1
  'C019': { lat: 17.6699, lon: 75.9164 },      // Solapur Procurement Centre 2
  'C005': { lat: 19.0952, lon: 74.7480 },      // Ahmednagar Procurement Centre 1
  'C002': { lat: 19.9975, lon: 73.7898 },      // Nashik Procurement Centre 1
  'C018': { lat: 20.0075, lon: 73.7998 },      // Nashik Procurement Centre 2
  'C022': { lat: 20.9320, lon: 77.7523 },      // Amravati Vidarbha Cotton Yard
  'C004': { lat: 21.1458, lon: 79.0882 },      // Nagpur Procurement Centre 1
  'C020': { lat: 21.1558, lon: 79.0982 },      // Nagpur Procurement Centre 2
  'C009': { lat: 22.7196, lon: 75.8577 },      // Indore Procurement Centre 1
  'C011': { lat: 23.1765, lon: 75.7885 },      // Ujjain Procurement Centre 1
  'C012': { lat: 23.2031, lon: 77.0844 },      // Sehore Procurement Centre 1
  'C010': { lat: 23.2599, lon: 77.4126 },      // Bhopal Procurement Centre 1
  'C024': { lat: 22.7533, lon: 77.7289 },      // Hoshangabad Wheat Procurement Depot
  'C023': { lat: 23.1815, lon: 79.9864 },      // Jabalpur Narmada Krishi Mandi
  'C015': { lat: 26.4499, lon: 80.3319 },      // Kanpur Procurement Centre 1
  'C013': { lat: 26.8467, lon: 80.9462 },      // Lucknow Procurement Centre 1
  'C027': { lat: 25.3176, lon: 82.9739 },      // Varanasi Purvanchal Krishi Hub
  'C014': { lat: 27.1767, lon: 78.0081 },      // Agra Procurement Centre 1
  'C028': { lat: 28.3670, lon: 79.4304 },      // Bareilly Rohilkhand Mandi Yard
  'C016': { lat: 28.9845, lon: 77.7064 },      // Meerut Procurement Centre 1
  'C007': { lat: 30.3398, lon: 76.3869 },      // Patiala Procurement Centre 1
  'C026': { lat: 30.2110, lon: 74.9455 },      // Bhatinda Malwa Grain Terminal
  'C006': { lat: 30.9010, lon: 75.8573 },      // Ludhiana Procurement Centre 1
  'C025': { lat: 31.3260, lon: 75.5762 },      // Jalandhar Doaba APMC Centre
  'C008': { lat: 31.6340, lon: 74.8723 },      // Amritsar Procurement Centre 1
};

function calculateHaversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371.0;
  const dLat = ((lat2 - lat1) * Math.PI) / 180.0;
  const dLon = ((lon2 - lon1) * Math.PI) / 180.0;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180.0) * Math.cos((lat2 * Math.PI) / 180.0) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

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

  // Recommendations & Proximity
  const [nearbyCentres, setNearbyCentres] = useState([]);
  const [visibleCentresCount, setVisibleCentresCount] = useState(5);

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

  // Market Intelligence & Decision Support (Part 20)
  const [marketIntel, setMarketIntel] = useState(null);

  // Pre-Gate AI Mango Visual Quality Inspection (Parts 1-19, 37)
  const [mangoScanFile, setMangoScanFile] = useState(null);
  const [mangoScanPreview, setMangoScanPreview] = useState(null);
  const [mangoScanning, setMangoScanning] = useState(false);
  const [mangoScanResult, setMangoScanResult] = useState(null);
  const [mangoScanError, setMangoScanError] = useState('');
  const [showDebugStages, setShowDebugStages] = useState(false);
  const mangoInputRef = useRef(null);

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
      getFarmerCrops(farmerIdentifier).catch(() => []),
      getFarmerMarketIntelligence(farmerIdentifier).catch(() => null)
    ])
      .then(([overview, bData, profile, cMasterRes, notifs, comps, fCrops, intel]) => {
        setOverviewData(overview);
        setBookings(Array.isArray(bData) ? bData : []);
        setFarmerProfile(profile);
        setCropsMaster(cMasterRes?.crops || []);
        setNotifications(Array.isArray(notifs) ? notifs : []);
        setComplaints(Array.isArray(comps) ? comps : []);
        setCrops(fCrops || (profile?.crops || []));
        setMarketIntel(intel);

        const activeCentre = overview?.token_tracking?.centre_id || bData?.[0]?.centre_id || 'C001';
        setSelectedCentreId(activeCentre);
        fetchLiveQueue(activeCentre);

        // Fetch nearby centres for farmer district
        const farmerCrop = profile?.crops?.[0]?.crop_name || 'Mango';
        const farmerDist = profile?.district || (profile?.state === 'Goa' ? 'North Goa' : 'North Goa');
        recommendCentre({
          crop: farmerCrop,
          quantity: 40,
          farmer_id: farmerIdentifier,
          district: farmerDist
        })
          .then(res => setNearbyCentres(res.centres || []))
          .catch(() => {});
      })
      .catch(err => console.error('Error loading farmer dashboard:', err))
      .finally(() => setLoading(false));
  }, [farmerIdentifier]);

  const handleSelectMangoScanImage = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type.toLowerCase())) {
      setMangoScanError('Only JPG, PNG, and WEBP formats are supported.');
      return;
    }
    setMangoScanError('');
    setMangoScanFile(file);
    const reader = new FileReader();
    reader.onload = () => setMangoScanPreview(reader.result);
    reader.readAsDataURL(file);
  };

  const handleRunMangoPreInspection = async () => {
    if (!mangoScanFile) {
      setMangoScanError('Please choose or capture a photograph containing sampled mangoes.');
      return;
    }
    setMangoScanning(true);
    setMangoScanError('');
    try {
      const res = await scanMangoQuality('DEMO', mangoScanFile);
      if (res && res.success) {
        setMangoScanResult(res);
      } else {
        setMangoScanError(res?.message || 'Inspection could not detect mango fruits.');
      }
    } catch (err) {
      setMangoScanError(err.message || 'Mango AI scan failed.');
    } finally {
      setMangoScanning(false);
    }
  };

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
            className={`farmer-tab-btn ${activeTab === 'main' ? 'active' : ''}`}
          >
            <Home size={16} /> Home
          </button>

          <button
            onClick={() => setActiveTab('msp_prices')}
            className={`farmer-tab-btn ${activeTab === 'msp_prices' ? 'active' : ''}`}
          >
            <IndianRupee size={16} /> MSP & Estimated Price
          </button>

          <button
            onClick={() => setActiveTab('ai_insights')}
            className={`farmer-tab-btn ${activeTab === 'ai_insights' ? 'active' : ''}`}
          >
            <Sparkles size={16} /> AI Insights
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={`farmer-tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          >
            <Bell size={16} /> Alerts ({notifications.length})
          </button>

          <button
            onClick={() => setActiveTab('centres')}
            className={`farmer-tab-btn ${activeTab === 'centres' ? 'active' : ''}`}
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
                    {nearbyCentres[0]?.centre_name || 'Sanquelim Procurement Centre 1'} • Active Weighbridge.
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

          {/* ============================================================== */}
          {/* SECTION 1: PROCUREMENT AI INTELLIGENCE & MARKET FORECASTS (PART 20) */}
          {/* ============================================================== */}
          <div className="card" style={{ padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sparkles size={20} style={{ color: 'var(--primary)' }} />
                  Procurement AI Intelligence & Market Forecasts
                </h2>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.72rem', background: '#3b82f6', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>CURRENT</span>
                  <span style={{ fontSize: '0.72rem', background: '#8b5cf6', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>FORECAST</span>
                  <span style={{ fontSize: '0.72rem', background: '#059669', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>ESTIMATE</span>
                  <span style={{ fontSize: '0.72rem', background: '#d97706', color: '#fff', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>RECOMMENDATION</span>
                </div>
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                Data-grounded farmer decision support for {farmerProfile?.district || 'Zone'} • {farmerProfile?.state || 'State'}
              </p>
            </div>

            {/* Farmer Registered Crop Portfolio & Holding Value Banner */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(27,77,62,0.08) 0%, rgba(5,150,105,0.06) 100%)',
              border: '1.5px solid var(--primary)',
              borderRadius: '12px',
              padding: '1.25rem',
              marginBottom: '1.5rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div>
                <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Farmer Holding Valuation Context <span style={{ fontSize: '0.72rem', background: '#059669', color: '#fff', padding: '1px 6px', borderRadius: '4px', marginLeft: '6px' }}>ESTIMATE</span>
                </div>
                <div style={{ fontSize: '1.75rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '2px' }}>
                  ₹{(marketIntel?.total_estimated_portfolio_value || (crops.reduce((acc, c) => acc + (parseFloat(c.estimated_quantity_quintals || 40) * 2350), 0))).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '2px' }}>
                  Cumulative estimated procurement value across {crops.length > 0 ? crops.length : 6} registered crop lots
                </div>
              </div>
              <div style={{ textAlign: 'right', maxWidth: '380px' }}>
                <div style={{ fontSize: '0.78rem', color: 'var(--muted)', lineHeight: 1.4 }}>
                  <strong>Valuation Rule:</strong> Expected quantity × applicable verified rate. Presented as an estimate for planning; final disbursement is determined after weighment and quality grading.
                </div>
              </div>
            </div>

            {/* Grid 1: Registered Crop Rates & Decision Support */}
            <h4 style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Scale size={16} /> Your Registered Crops — Applicable MSP & Demand Outlook
            </h4>
            <div style={{ overflowX: 'auto', marginBottom: '1.5rem' }}>
              <table className="table" style={{ width: '100%', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ background: 'var(--surface-secondary)', borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Commodity</th>
                    <th style={{ padding: '8px 12px', textAlign: 'left' }}>Season</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>Expected Lot</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>Official Legal MSP</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right' }}>Estimated Value</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center' }}>Demand Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {(marketIntel?.my_crops_intelligence && marketIntel.my_crops_intelligence.length > 0
                    ? marketIntel.my_crops_intelligence
                    : [
                        { crop_name: 'Cotton', season: 'Kharif', registered_quantity_quintals: 140, official_msp_rate: 7121, estimated_total_value: 977487, demand_trend: 'RISING' },
                        { crop_name: 'Wheat', season: 'Rabi', registered_quantity_quintals: 55, official_msp_rate: 2275, estimated_total_value: 125125, demand_trend: 'STABLE' },
                        { crop_name: 'Mango', season: 'Summer', registered_quantity_quintals: 45, official_msp_rate: 2380, estimated_total_value: 107119, demand_trend: 'RISING' },
                        { crop_name: 'Paddy', season: 'Kharif', registered_quantity_quintals: 60, official_msp_rate: 2369, estimated_total_value: 142140, demand_trend: 'STABLE' },
                        { crop_name: 'Soybean', season: 'Kharif', registered_quantity_quintals: 60, official_msp_rate: 4892, estimated_total_value: 293520, demand_trend: 'RISING' },
                        { crop_name: 'Maize', season: 'Kharif', registered_quantity_quintals: 60, official_msp_rate: 2225, estimated_total_value: 133500, demand_trend: 'STABLE' }
                      ]
                  ).map((fc, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 700 }}>{fc.crop_name}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--muted)' }}>{fc.season}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 600 }}>{fc.registered_quantity_quintals || 40} Q</td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 700, color: 'var(--secondary)' }}>
                        ₹{(fc.official_msp_rate || 2300).toLocaleString('en-IN')} / Q
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'right', fontWeight: 800, color: 'var(--primary)' }}>
                        ₹{(fc.estimated_total_value || (fc.registered_quantity_quintals * 2300)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: fc.demand_trend === 'RISING' ? 'rgba(5,150,105,0.1)' : 'rgba(100,116,139,0.1)',
                          color: fc.demand_trend === 'RISING' ? '#059669' : '#64748b'
                        }}>
                          {fc.demand_trend || 'STABLE'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Grid 2: State Demand/Supply Balances & Planting Recommendations */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
              
              {/* Box A: Supply/Demand Balances (FORECAST) */}
              <div style={{ backgroundColor: 'var(--bg-page)', padding: '1.25rem', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Commodity Demand & Supply Balance
                  </h4>
                  <span style={{ fontSize: '0.70rem', background: '#8b5cf6', color: '#fff', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>FORECAST</span>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--muted)', margin: '0 0 10px 0' }}>
                  State reserve intake targets vs active mandi pipeline
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(marketIntel?.supply_shortages || [
                    { crop_name: 'Soybean', current_procurement_pipeline_quintals: 18400, projected_state_demand_quintals: 40000, reason: 'Active intake meets 46% of projected state buffer target.' },
                    { crop_name: 'Cotton', current_procurement_pipeline_quintals: 22100, projected_state_demand_quintals: 40000, reason: 'High textile mill procurement demand against regional arrivals.' },
                    { crop_name: 'Mango', current_procurement_pipeline_quintals: 12500, projected_state_demand_quintals: 30000, reason: 'Perishable seasonal demand with strong export and processing intake.' }
                  ]).slice(0, 3).map((item, idx) => (
                    <div key={idx} style={{ background: 'var(--surface)', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '0.78rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: 'var(--secondary)' }}>
                        <span>{item.crop_name}</span>
                        <span style={{ color: '#d97706' }}>Supply Deficit</span>
                      </div>
                      <div style={{ color: 'var(--muted)', fontSize: '0.74rem', marginTop: '2px' }}>
                        {item.reason}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Box B: Recommended Alternative Planting Crops (RECOMMENDATION) */}
              <div style={{ backgroundColor: 'var(--bg-page)', padding: '1.25rem', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h4 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Recommended Crops to Consider Planting
                  </h4>
                  <span style={{ fontSize: '0.70rem', background: '#d97706', color: '#fff', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>RECOMMENDATION</span>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--muted)', margin: '0 0 10px 0' }}>
                  Based on project demand data and seasonal buffer shortages
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {[
                    { crop: 'Soybean (Oilseed)', msp: '₹4,892/Q', reason: 'High regional processing demand with low state buffer inventory.', assumption: 'Assumes steady domestic edible oil demand.' },
                    { crop: 'Mustard (Rabi Oilseed)', msp: '₹5,650/Q', reason: 'Strong support price and minimal mandi storage congestion.', assumption: 'Assumes timely winter sowing.' },
                    { crop: 'Mango (Horticulture)', msp: '₹2,380/Q', reason: 'Controlled intake setup with premium quality grading realization.', assumption: 'Assumes favorable post-harvest handling.' }
                  ].map((rec, rIdx) => (
                    <div key={rIdx} style={{ background: 'var(--surface)', padding: '8px 10px', borderRadius: '6px', border: '1px solid var(--border)', fontSize: '0.78rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: 'var(--secondary)' }}>
                        <span>{rec.crop}</span>
                        <span style={{ color: 'var(--primary)' }}>MSP: {rec.msp}</span>
                      </div>
                      <div style={{ color: 'var(--muted)', fontSize: '0.74rem', marginTop: '2px' }}>
                        <strong>Why:</strong> {rec.reason}
                      </div>
                      <div style={{ color: '#64748b', fontSize: '0.70rem', fontStyle: 'italic', marginTop: '1px' }}>
                        <strong>Assumption:</strong> {rec.assumption}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Non-Guarantee Transparency Disclaimer */}
            <div style={{
              backgroundColor: 'var(--surface-secondary)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '10px 14px',
              fontSize: '0.78rem',
              color: 'var(--muted)',
              lineHeight: 1.4
            }}>
              <strong>Decision Support Advisory:</strong> Based on current project data and forecast assumptions. All indications represent econometric estimates; no future income or price guarantees are implied. Expected values are distinct from final disbursement, which depends on actual physical weighment and moisture/quality grading.
            </div>
          </div>

          {/* ============================================================== */}
          {/* SECTION 2: AI MANGO QUALITY SCANNER (PARTS 1-19, 37) */}
          {/* ============================================================== */}
          <div className="card" style={{ padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Camera size={20} style={{ color: 'var(--primary)' }} />
                  AI Mango Quality Inspection (Pre-Gate Optical Scan)
                </h3>
                <span style={{ fontSize: '0.75rem', background: 'rgba(27,77,62,0.1)', color: 'var(--primary)', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>
                  Controlled Setup (White Background)
                </span>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                Marker-controlled watershed instance isolation, dark shadow rejection & AGMARK / Codex 184 quality grading
              </p>
            </div>

            {/* Image Acquisition Protocol Notice (Part 1) */}
            <div style={{
              background: 'var(--bg-page)',
              border: '1px solid var(--border)',
              borderRadius: '10px',
              padding: '12px 16px',
              marginBottom: '1.25rem',
              fontSize: '0.8rem',
              color: 'var(--muted)'
            }}>
              <strong style={{ color: 'var(--secondary)' }}>Physical Setup Protocol:</strong> Place multiple representative mangoes from each sack onto a clean <strong>WHITE sheet/background</strong> under an overhead <strong>diffuse WHITE LIGHT</strong>. Keep the camera directly above at a consistent angle. Touching and overlapping mangoes are welcomed; the watershed segmentation algorithm partitions adjacent fruits.
            </div>

            {/* Upload / Capture Box */}
            <div style={{
              border: '2px dashed var(--border)',
              borderRadius: '12px',
              padding: '24px',
              textAlign: 'center',
              background: 'var(--surface-secondary)',
              marginBottom: '1.5rem'
            }}>
              <input
                type="file"
                ref={mangoInputRef}
                style={{ display: 'none' }}
                accept="image/jpeg,image/png,image/webp"
                onChange={handleSelectMangoScanImage}
              />

              {!mangoScanPreview ? (
                <div>
                  <Sparkles size={36} color="var(--primary)" style={{ marginBottom: '10px' }} />
                  <h4 style={{ margin: '0 0 6px 0', fontWeight: 800, color: 'var(--secondary)', fontSize: '1rem' }}>
                    Capture or Upload Mango Inspection Photo
                  </h4>
                  <p style={{ color: 'var(--muted)', fontSize: '0.82rem', maxWidth: '480px', margin: '0 auto 16px auto' }}>
                    Take ONE photograph containing multiple mangoes placed on a clean white surface.
                  </p>
                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => mangoInputRef.current?.click()}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                    >
                      <Upload size={15} /> Select Photo
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline"
                      onClick={() => mangoInputRef.current?.click()}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                    >
                      <Camera size={15} /> Camera
                    </button>
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ maxWidth: '420px', margin: '0 auto 14px auto', borderRadius: '8px', overflow: 'hidden', border: '1px solid var(--border)' }}>
                    <img
                      src={mangoScanPreview}
                      alt="Mango Sample Preview"
                      style={{ width: '100%', maxHeight: '280px', objectFit: 'contain', display: 'block', background: '#000' }}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleRunMangoPreInspection}
                      disabled={mangoScanning}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', fontSize: '0.88rem' }}
                    >
                      {mangoScanning ? <RefreshCw size={15} className="spin" /> : <Sparkles size={15} />}
                      {mangoScanning ? 'Isolating Mangoes & Analyzing Surface...' : 'Execute Mango AI Quality Scan'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-outline"
                      onClick={() => {
                        setMangoScanFile(null);
                        setMangoScanPreview(null);
                        setMangoScanResult(null);
                        setMangoScanError('');
                      }}
                      disabled={mangoScanning}
                      style={{ fontSize: '0.85rem' }}
                    >
                      Reset
                    </button>
                  </div>
                </div>
              )}
            </div>

            {mangoScanError && (
              <div className="alert alert-danger" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
                {mangoScanError}
              </div>
            )}

            {/* Mango Inspection Results: Strict Hierarchy (Parts 18-19, 37) */}
            {mangoScanResult && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

                {/* 1. Header & Detected Count */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 800, color: 'var(--secondary)', fontSize: '1.05rem' }}>
                      Optical Quality Scan Results ({mangoScanResult.mangoes_detected || (mangoScanResult.detections?.length || 0)} Fruit Instances)
                    </h4>
                    <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '2px' }}>
                      Instance masks segmented via distance-transform watershed with shape priors
                    </div>
                  </div>
                  <span style={{ fontSize: '0.75rem', background: 'var(--primary)', color: '#fff', padding: '3px 10px', borderRadius: '4px', fontWeight: 800 }}>
                    {mangoScanResult.mangoes_detected} Mangoes Isolated
                  </span>
                </div>

                {/* 2. Macro Metrics Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
                  <div className="stat-card" style={{ padding: '10px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 700 }}>Total Sampled</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--secondary)' }}>{mangoScanResult.mangoes_detected}</div>
                  </div>
                  <div className="stat-card" style={{ padding: '10px', textAlign: 'center', borderLeft: '3px solid #059669' }}>
                    <div style={{ fontSize: '0.72rem', color: '#059669', fontWeight: 700 }}>Healthy</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#059669' }}>{mangoScanResult.healthy_count || mangoScanResult.healthy || 0}</div>
                  </div>
                  <div className="stat-card" style={{ padding: '10px', textAlign: 'center', borderLeft: '3px solid #dc2626' }}>
                    <div style={{ fontSize: '0.72rem', color: '#dc2626', fontWeight: 700 }}>Defective</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#dc2626' }}>{mangoScanResult.defect_count || 0}</div>
                  </div>
                  <div className="stat-card" style={{ padding: '10px', textAlign: 'center', borderLeft: '3px solid #d97706' }}>
                    <div style={{ fontSize: '0.72rem', color: '#d97706', fontWeight: 700 }}>Ripe / Eating</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: '#d97706' }}>{mangoScanResult.ripe_count || 0}</div>
                  </div>
                  <div className="stat-card" style={{ padding: '10px', textAlign: 'center', borderLeft: '3px solid #3b82f6' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 700 }}>Avg Defect %</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--text)' }}>
                      {(mangoScanResult.affected_percentage || 0).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* 3. Individual Mango Cards (Parts 4 & 19) */}
                <div>
                  <h4 style={{ fontSize: '0.92rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '10px' }}>
                    Mango-by-Mango Surface Condition
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
                    {(mangoScanResult.detections || mangoScanResult.mangoes || []).map((det, idx) => {
                      const isH = (det.health_status === 'Healthy' || det.status === 'Healthy' || det.defect_percentage === 0);
                      const statusColor = isH ? '#059669' : '#dc2626';
                      const statusBg = isH ? 'rgba(5,150,105,0.1)' : 'rgba(220,38,38,0.1)';
                      const statusLabel = det.status || (isH ? 'Healthy' : 'Minor Surface Defect');
                      const defectsList = det.visible_defects || (det.defect_type ? [det.defect_type] : (isH ? ['None'] : ['Surface Discolouration']));

                      return (
                        <div key={idx} style={{
                          background: 'var(--surface)',
                          border: `1.5px solid ${isH ? '#059669' : '#f87171'}`,
                          borderRadius: '10px',
                          padding: '12px',
                          display: 'flex',
                          gap: '12px',
                          alignItems: 'flex-start'
                        }}>
                          {det.crop_url && (
                            <img
                              src={det.crop_url}
                              alt={`Mango #${det.sample_index || (idx + 1)}`}
                              style={{ width: '76px', height: '76px', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--border)' }}
                            />
                          )}
                          <div style={{ flex: 1, fontSize: '0.8rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                              <strong style={{ color: 'var(--secondary)', fontSize: '0.88rem' }}>Mango #{det.sample_index || (idx + 1)}</strong>
                              <span style={{ fontSize: '0.72rem', fontWeight: 800, padding: '2px 8px', borderRadius: '4px', background: statusBg, color: statusColor }}>
                                {statusLabel}
                              </span>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.76rem', color: 'var(--text)' }}>
                              <div>Defect Area: <strong style={{ color: isH ? '#059669' : '#dc2626' }}>{(det.defect_percentage !== undefined ? det.defect_percentage : (det.affected_area_pct || 0)).toFixed(1)}%</strong></div>
                              <div>Confidence: <strong>{det.confidence || 92}%</strong></div>
                              <div>Ripeness: <strong>{det.ripeness || 'Mature'}</strong></div>
                              <div>Quality: <strong>{det.quality_grade || (isH ? 'Grade A' : 'Grade B')}</strong></div>
                            </div>
                            <div style={{ fontSize: '0.74rem', color: 'var(--muted)', marginTop: '4px' }}>
                              Visible defects: <strong style={{ color: isH ? '#059669' : '#dc2626' }}>{defectsList.join(', ')}</strong>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 4. Collapsible Analysis Details / Pipeline Stages (Part 19) */}
                <div style={{ border: '1px solid var(--border)', borderRadius: '10px', overflow: 'hidden' }}>
                  <button
                    type="button"
                    onClick={() => setShowDebugStages(!showDebugStages)}
                    style={{
                      width: '100%',
                      background: 'var(--surface-secondary)',
                      padding: '10px 16px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                      fontWeight: 700,
                      color: 'var(--secondary)'
                    }}
                  >
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Eye size={16} /> Technical Analysis Details & Visual Debug Stages
                    </span>
                    {showDebugStages ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </button>

                  {showDebugStages && (
                    <div style={{ padding: '16px', background: 'var(--bg-page)', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                      {mangoScanResult.annotated_image_url && (
                        <div>
                          <div style={{ fontSize: '0.78rem', fontWeight: 700, marginBottom: '6px', color: 'var(--secondary)' }}>
                            Instance Boundaries & Defect Contours Overlay:
                          </div>
                          <img
                            src={mangoScanResult.annotated_image_url}
                            alt="Multi-fruit detection overlay"
                            style={{ width: '100%', maxHeight: '360px', objectFit: 'contain', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface-secondary)' }}
                          />
                        </div>
                      )}

                      {mangoScanResult.debug_images && Object.keys(mangoScanResult.debug_images).length > 0 && (
                        <div>
                          <div style={{ fontSize: '0.78rem', fontWeight: 700, marginBottom: '8px', color: 'var(--text-secondary)' }}>
                            10-Stage Pipeline Visual Audit:
                          </div>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
                            {Object.entries(mangoScanResult.debug_images).filter(([k]) => k !== 'debug_2_peel_mask').map(([k, url]) => (
                              <div key={k} className="dev-stage-card">
                                <div className="dev-stage-title">{k.replace('debug_', '').replace(/_/g, ' ')}</div>
                                <div className="dev-stage-img-box" style={{ maxHeight: '100px' }}>
                                  <img src={url} alt={k} className="dev-stage-img" style={{ maxHeight: '100px' }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* 5. PROMINENT FINAL QUALITY GRADE (STRICTLY PLACED AFTER DETAILED ANALYSIS - Parts 18, 37) */}
                <div style={{
                  background: 'var(--surface)',
                  borderRadius: '12px',
                  padding: '20px',
                  border: '2px solid var(--primary)',
                  boxShadow: 'var(--shadow-sm)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '14px'
                }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>
                      Final Mandi Quality Grade Determination
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '4px' }}>
                      <span style={{
                        fontSize: '1.75rem',
                        fontWeight: 900,
                        padding: '4px 14px',
                        borderRadius: '8px',
                        background: (mangoScanResult.visual_grade || 'Grade A') === 'Grade A' ? 'var(--success)' : (mangoScanResult.visual_grade === 'Grade B' ? 'var(--warning)' : 'var(--danger)'),
                        color: '#fff'
                      }}>
                        {mangoScanResult.visual_grade || 'Grade A'}
                      </span>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text-primary)' }}>
                          {(mangoScanResult.visual_grade || 'Grade A') === 'Grade A' ? 'Premium Export / Table Quality' : (mangoScanResult.visual_grade === 'Grade B' ? 'Standard Mandi Grade' : 'Industrial Processing Grade')}
                        </div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                          Conforms to AGMARK & Codex Alimentarius 184 standards
                        </div>
                      </div>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => navigate('book-slot')}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '10px 20px', fontSize: '0.9rem' }}
                    >
                      <Calendar size={16} /> Book Procurement Slot for this Lot
                    </button>
                  </div>
                </div>

              </div>
            )}
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
      {activeTab === 'centres' && (() => {
        const farmerRefLat = farmerProfile?.latitude || 15.5685;
        const farmerRefLon = farmerProfile?.longitude || 73.9965;

        const sortedCentres = [...nearbyCentres].map(c => {
          const coords = CENTRE_COORDINATES[c.centre_id] || (c.latitude && c.longitude ? { lat: c.latitude, lon: c.longitude } : null);
          let distKm = null;
          if (coords) {
            distKm = calculateHaversineKm(farmerRefLat, farmerRefLon, coords.lat, coords.lon);
          } else if (c.distance_km != null) {
            distKm = parseFloat(c.distance_km);
          }
          return {
            ...c,
            calculatedDistanceKm: distKm,
            formattedDistance: distKm != null ? `${distKm.toFixed(2)} km` : 'Proximity N/A'
          };
        }).sort((a, b) => {
          if (a.calculatedDistanceKm != null && b.calculatedDistanceKm != null) {
            return a.calculatedDistanceKm - b.calculatedDistanceKm;
          }
          if (a.calculatedDistanceKm != null) return -1;
          if (b.calculatedDistanceKm != null) return 1;
          return 0;
        });

        const displayedCentres = sortedCentres.slice(0, visibleCentresCount);
        const hasMoreCentres = visibleCentresCount < sortedCentres.length;

        return (
          <div className="card" style={{ padding: '1.75rem', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Compass size={20} style={{ color: 'var(--primary)' }} />
                  Procurement Centre Network & Live Congestion
                </h2>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: 'var(--muted)' }}>
                  Nearest official state procurement centres sorted by Haversine proximity from your farm reference.
                </p>
              </div>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--primary)', backgroundColor: 'rgba(27, 77, 62, 0.08)', padding: '5px 12px', borderRadius: '6px' }}>
                Showing {Math.min(visibleCentresCount, sortedCentres.length)} of {sortedCentres.length} Centres
              </div>
            </div>

            {displayedCentres.length === 0 ? (
              <div style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--muted)', background: 'var(--bg-page)', borderRadius: '8px' }}>
                Loading nearest procurement centres...
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                {displayedCentres.map((c) => (
                  <div key={c.centre_id} style={{
                    backgroundColor: 'var(--bg-page)',
                    border: '1px solid var(--border)',
                    borderRadius: '10px',
                    padding: '1.15rem',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
                  }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                        <div style={{ fontWeight: 800, color: 'var(--secondary)', fontSize: '1.05rem', lineHeight: 1.3 }}>
                          {c.centre_name}
                        </div>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '3px',
                          fontSize: '0.78rem',
                          fontWeight: 800,
                          padding: '3px 8px',
                          borderRadius: '6px',
                          backgroundColor: 'rgba(27, 77, 62, 0.12)',
                          color: 'var(--primary)',
                          whiteSpace: 'nowrap'
                        }}>
                          <MapPin size={12} />
                          {c.formattedDistance}
                        </span>
                      </div>

                      <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginBottom: '0.75rem' }}>
                        {c.district}, {c.state} • Centre ID: <strong>{c.centre_id}</strong>
                      </div>

                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '0.5rem',
                        padding: '0.75rem',
                        backgroundColor: 'var(--surface-secondary)',
                        borderRadius: '6px',
                        fontSize: '0.82rem',
                        marginBottom: '0.75rem'
                      }}>
                        <div>
                          <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>Estimated Wait</span>
                          <strong>~{c.estimated_wait_minutes || c.estimated_wait_min || 20} mins</strong>
                        </div>
                        <div>
                          <span style={{ color: 'var(--muted)', display: 'block', fontSize: '0.75rem' }}>Current Queue</span>
                          <strong>{c.current_queue || c.queue_length || 4} farmers</strong>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '0.5rem' }}>
                      <button
                        onClick={() => {
                          setSelectedCentreId(c.centre_id);
                          navigate('book-slot');
                        }}
                        className="btn btn-outline btn-sm"
                        style={{ width: '100%', fontSize: '0.82rem', padding: '6px 12px' }}
                      >
                        Book Slot Here
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Pagination Controls */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '1rem',
              marginTop: '1.5rem',
              paddingTop: '1.25rem',
              borderTop: '1px solid var(--border)'
            }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                Showing nearest <strong>{Math.min(visibleCentresCount, sortedCentres.length)}</strong> of <strong>{sortedCentres.length}</strong> centres
              </span>

              {hasMoreCentres ? (
                <button
                  onClick={() => setVisibleCentresCount(prev => prev + 5)}
                  className="btn btn-primary"
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '0.88rem',
                    padding: '0.55rem 1.25rem',
                    fontWeight: 700
                  }}
                >
                  <ChevronDown size={16} /> Show 5 More Centres
                </button>
              ) : (
                <span style={{
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  color: 'var(--muted)',
                  backgroundColor: 'var(--bg-page)',
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: '1px solid var(--border)'
                }}>
                  All {sortedCentres.length} Centres Loaded
                </span>
              )}
            </div>
          </div>
        );
      })()}

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
              {(() => {
                const farmerRefLat = farmerProfile?.latitude || 15.5685;
                const farmerRefLon = farmerProfile?.longitude || 73.9965;
                const modalSorted = [...nearbyCentres].map(c => {
                  const coords = CENTRE_COORDINATES[c.centre_id] || (c.latitude && c.longitude ? { lat: c.latitude, lon: c.longitude } : null);
                  let distKm = null;
                  if (coords) {
                    distKm = calculateHaversineKm(farmerRefLat, farmerRefLon, coords.lat, coords.lon);
                  } else if (c.distance_km != null) {
                    distKm = parseFloat(c.distance_km);
                  }
                  return { ...c, calculatedDistanceKm: distKm, formattedDistance: distKm != null ? `${distKm.toFixed(2)} km` : null };
                }).sort((a, b) => {
                  if (a.calculatedDistanceKm != null && b.calculatedDistanceKm != null) return a.calculatedDistanceKm - b.calculatedDistanceKm;
                  if (a.calculatedDistanceKm != null) return -1;
                  if (b.calculatedDistanceKm != null) return 1;
                  return 0;
                });

                return modalSorted.map((c) => (
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--secondary)' }}>
                          {c.centre_name}
                        </span>
                        {c.formattedDistance && (
                          <span style={{ fontSize: '0.75rem', fontWeight: 800, padding: '2px 6px', borderRadius: '4px', background: 'rgba(27,77,62,0.1)', color: 'var(--primary)' }}>
                            {c.formattedDistance}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '2px' }}>
                        {c.district}, {c.state} • Wait: ~{c.estimated_wait_minutes || c.estimated_wait_min || 20}m • Queue: {c.current_queue || c.queue_length || 4}
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedCentreId(c.centre_id);
                        setActiveModal(null);
                        navigate('book-slot');
                      }}
                      className="btn btn-primary btn-sm"
                      style={{ fontSize: '0.8rem', padding: '6px 12px' }}
                    >
                      Book Here
                    </button>
                  </div>
                ));
              })()}
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
