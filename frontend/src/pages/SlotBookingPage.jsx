import React, { useEffect, useState } from 'react';
import {
  getCentres, getSlots, bookSlot, getCentreDetails, getOperatingConfig,
  getDailyCapacity, getEstimatedPrice, recommendCentre, getRecommendedSlots
} from '../services/api';
import {
  Calendar, Clock, MapPin, Wheat, AlertCircle, ArrowLeft, Scale,
  CheckCircle2, Info, TrendingUp, Sparkles, Navigation, Users, Check, ChevronRight
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';
import DateInput from '../components/DateInput';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const parseDaysArray = (daysVal) => {
  if (daysVal === '[object Object]') {
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  }
  let raw = [];
  if (Array.isArray(daysVal)) {
    raw = daysVal;
  } else if (typeof daysVal === 'string' && daysVal.trim()) {
    raw = daysVal.split(',').map(d => d.trim()).filter(Boolean);
  } else {
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  }

  const matched = [];
  for (const item of raw) {
    const found = WEEKDAYS.find(w => w.toLowerCase() === String(item).toLowerCase());
    if (found && !matched.includes(found)) {
      matched.push(found);
    }
  }
  return matched;
};

const STATE_CROP_RULES = {
  'Maharashtra': ['Paddy', 'Wheat', 'Cotton', 'Soybean', 'Maize'],
  'Punjab': ['Paddy', 'Wheat', 'Cotton', 'Soybean', 'Maize'],
  'Madhya Pradesh': ['Paddy', 'Wheat', 'Cotton', 'Soybean', 'Maize'],
  'Uttar Pradesh': ['Paddy', 'Wheat', 'Cotton', 'Soybean', 'Maize'],
  'Goa': ['Mango', 'Banana', 'Tomato']
};

export default function SlotBookingPage({ user, onBookingSuccess, navigate }) {
  const [selectedState, setSelectedState] = useState('Maharashtra');
  const [centres, setCentres] = useState([]);
  const [selectedCentreId, setSelectedCentreId] = useState('');
  const [currentCentreDetails, setCurrentCentreDetails] = useState(null);

  const todayStr = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(todayStr);

  const [supportedCropsList, setSupportedCropsList] = useState(STATE_CROP_RULES['Maharashtra']);
  const [crop, setCrop] = useState('Wheat');
  const [quantity, setQuantity] = useState('42');

  // Intelligent Recommendations
  const [recommendedCentres, setRecommendedCentres] = useState([]);
  const [recommendedSlots, setRecommendedSlots] = useState([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [showAdvancedInfo, setShowAdvancedInfo] = useState(false);

  // Price & MSP
  const [priceInfo, setPriceInfo] = useState(null);
  const [loadingPrice, setLoadingPrice] = useState(false);

  // Slots & Capacity
  const [slots, setSlots] = useState([]);
  const [selectedSlotId, setSelectedSlotId] = useState(null);
  const [operatingConfig, setOperatingConfig] = useState({ operating_days: [], non_operational_dates: [] });
  const [dailyCapacityInfo, setDailyCapacityInfo] = useState(null);

  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [noticeInfo, setNoticeInfo] = useState(null);
  const [showSummaryModal, setShowSummaryModal] = useState(false);

  // Fetch list of procurement centres
  useEffect(() => {
    getCentres()
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setCentres(list);
        if (list.length > 0) {
          const defaultCentre = list.find(c => c.centre_id === 'C001') || list[0];
          setSelectedCentreId(defaultCentre.centre_id);
          setCurrentCentreDetails(defaultCentre);
          const cState = defaultCentre.state || 'Maharashtra';
          if (STATE_CROP_RULES[cState]) {
            setSelectedState(cState);
            setSupportedCropsList(STATE_CROP_RULES[cState]);
            setCrop(STATE_CROP_RULES[cState][0]);
          }
        }
      })
      .catch(() => setError('Unable to load procurement centres. Please try again.'));
  }, []);

  const handleStateChange = (newState) => {
    setSelectedState(newState);
    const validCrops = STATE_CROP_RULES[newState] || ['Paddy', 'Wheat', 'Cotton'];
    setSupportedCropsList(validCrops);
    if (!validCrops.includes(crop)) {
      setCrop(validCrops[0] || 'Wheat');
    }
    const matchingCentres = centres.filter(c => c.state?.toLowerCase() === newState.toLowerCase());
    if (matchingCentres.length > 0) {
      setSelectedCentreId(matchingCentres[0].centre_id);
      setCurrentCentreDetails(matchingCentres[0]);
    }
  };

  useEffect(() => {
    if (selectedCentreId && centres.length > 0) {
      const found = centres.find(c => c.centre_id === selectedCentreId);
      if (found) setCurrentCentreDetails(found);
    }
  }, [selectedCentreId, centres]);

  // Fetch Centre & Slot Recommendations
  useEffect(() => {
    if (crop && quantity) {
      setLoadingRecommendations(true);
      recommendCentre({
        crop,
        quantity: parseFloat(quantity) || 40,
        farmer_id: user?.user_id,
        district: user?.district || 'Pune'
      })
        .then(res => {
          setRecommendedCentres(res.centres || []);
        })
        .catch(() => setRecommendedCentres([]))
        .finally(() => setLoadingRecommendations(false));
    }
  }, [crop, quantity, user]);

  // Fetch Recommended Slots for selected centre and date
  useEffect(() => {
    if (selectedCentreId) {
      getRecommendedSlots(selectedCentreId, date)
        .then(res => {
          setRecommendedSlots(res.recommended_slots || []);
        })
        .catch(() => setRecommendedSlots([]));
    }
  }, [selectedCentreId, date]);

  // Fetch real-time official MSP & estimated price
  useEffect(() => {
    if (crop) {
      const qVal = parseFloat(quantity) > 0 ? parseFloat(quantity) : 42;
      setLoadingPrice(true);
      getEstimatedPrice({
        crop,
        quantity: qVal,
        centre_id: selectedCentreId
      })
        .then(data => setPriceInfo(data))
        .catch(() => setPriceInfo(null))
        .finally(() => setLoadingPrice(false));
    }
  }, [crop, quantity, selectedCentreId]);

  // Fetch slots, operating config, and daily capacity
  useEffect(() => {
    if (selectedCentreId && date) {
      setError('');
      setNoticeInfo(null);
      setSelectedSlotId(null);
      setLoadingSlots(true);

      Promise.all([
        getSlots(selectedCentreId, date),
        getOperatingConfig(selectedCentreId),
        getDailyCapacity(selectedCentreId, date),
        getRecommendedSlots(selectedCentreId, date).catch(() => null)
      ])
        .then(([slotsData, configData, capData, recData]) => {
          setOperatingConfig(configData);
          setDailyCapacityInfo(capData);
          if (recData && recData.recommended_slots) {
            setRecommendedSlots(recData.recommended_slots);
          }

          // 1. Holiday check
          const holidayMatch = (configData.non_operational_dates || []).find(d => d.date === date);
          if (holidayMatch) {
            setSlots([]);
            setNoticeInfo({ 
              type: 'closed', 
              message: `The procurement centre is not operational on the selected date (${holidayMatch.reason}).` 
            });
            return;
          }

          // 2. Weekly Operating Days
          const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
          const dateObj = new Date(date);
          const selectedDayName = dayNames[dateObj.getDay()];
          const opDays = parseDaysArray(configData.operating_days);

          const isAllowed = opDays.map(d => d.toLowerCase()).includes(selectedDayName.toLowerCase());
          if (!isAllowed) {
            setSlots([]);
            setNoticeInfo({ 
              type: 'closed', 
              message: `The procurement centre is not operational on the selected date (${selectedDayName} is a non-operating day).` 
            });
            return;
          }

          // 3. Daily Capacity Exhausted
          if (capData && capData.available_quintals <= 0) {
            setSlots(slotsData || []);
            setNoticeInfo({ 
              type: 'capacity_full', 
              message: `Daily quintal capacity has been reached for this date (0 Quintals available).` 
            });
            return;
          }

          // 4. No Slots Configured
          if (!slotsData || slotsData.length === 0) {
            setSlots([]);
            setNoticeInfo({ 
              type: 'empty', 
              message: `No time slots have been configured for this date.` 
            });
            return;
          }

          // Merge dynamic recommendation metadata into slots
          const dynamicSlots = recData?.slots || [];
          const enrichedSlots = (slotsData || []).map(s => {
            const match = dynamicSlots.find(ds => ds.slot_id === s.id || (ds.start_time === s.start_time && ds.end_time === s.end_time));
            if (match) {
              return {
                ...s,
                rank_type: match.rank_type,
                is_recommended: match.is_recommended,
                farmers_ahead: match.farmers_ahead,
                expected_wait_min: match.expected_wait_min,
                recommended_departure: match.recommended_departure,
                congestion: match.congestion,
                reason: match.reason
              };
            }
            return s;
          });

          // 5. Check All Slots Full
          if (enrichedSlots.every(s => s.is_full)) {
            setSlots(enrichedSlots);
            setNoticeInfo({ 
              type: 'slots_full', 
              message: `All time slots are currently full for this date.` 
            });
            return;
          }

          setSlots(enrichedSlots);
          // Auto-select top recommended slot or first available slot
          const topRec = enrichedSlots.find(s => s.rank_type === 'RECOMMENDED' && !s.is_full);
          const firstAvailable = topRec || enrichedSlots.find(s => !s.is_full);
          if (firstAvailable) {
            setSelectedSlotId(firstAvailable.id);
          }
        })
        .catch(() => {
          setSlots([]);
          setError('Unable to load slot information. Please try again.');
        })
        .finally(() => setLoadingSlots(false));
    }
  }, [selectedCentreId, date]);

  const handleReviewBooking = (e) => {
    e.preventDefault();
    setError('');

    const qty = parseFloat(quantity);
    if (isNaN(qty) || qty <= 0) {
      setError('Please enter a valid crop quantity in Quintals.');
      return;
    }

    if (!selectedSlotId) {
      setError('Please select an available time slot.');
      return;
    }

    if (dailyCapacityInfo && qty > dailyCapacityInfo.available_quintals) {
      setError(`Quantity exceeds daily available capacity! Max available for ${formatDateDisplay(date)} is ${dailyCapacityInfo.available_quintals} Quintals.`);
      return;
    }

    setShowSummaryModal(true);
  };

  const handleFinalConfirm = async () => {
    setSubmitting(true);
    setError('');

    try {
      const res = await bookSlot(
        user.user_id,
        selectedCentreId,
        selectedSlotId,
        crop,
        parseFloat(quantity)
      );
      setShowSummaryModal(false);
      const bookingData = res.booking || res;
      onBookingSuccess(bookingData);
    } catch (err) {
      setError(err.message || 'Booking failed.');
      setShowSummaryModal(false);
    } finally {
      setSubmitting(false);
    }
  };

  const currentSlotObj = slots.find(s => s.id === selectedSlotId);
  const bestRecommendedCentre = recommendedCentres[0];

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', paddingBottom: '3rem' }}>
      
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button 
          className="btn btn-outline"
          onClick={() => navigate('farmer-dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
            Procurement Slot Booking
          </h1>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--muted)' }}>
            Reserve your verified weighment appointment and receive a live digital queue token
          </p>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.25rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {noticeInfo && (
        <div className="alert alert-warning" style={{ 
          display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.25rem',
          background: noticeInfo.type === 'closed' ? '#fef2f2' : noticeInfo.type === 'capacity_full' ? '#fff7ed' : '#f8fafc',
          borderColor: noticeInfo.type === 'closed' ? '#fca5a5' : noticeInfo.type === 'capacity_full' ? '#ffedd5' : '#e2e8f0',
          color: noticeInfo.type === 'closed' ? '#991b1b' : noticeInfo.type === 'capacity_full' ? '#c2410c' : 'var(--secondary)'
        }}>
          <Info size={20} />
          <span style={{ fontWeight: 600 }}>{noticeInfo.message}</span>
        </div>
      )}

      <div className="card" style={{ padding: '2rem', border: '1px solid var(--border)', borderRadius: '16px' }}>
        <form onSubmit={handleReviewBooking}>
          
          {/* SECTION 1: FARMER DETAILS */}
          <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.75rem' }}>
              1. Farmer Details
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>Farmer Name</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={user?.name || 'Registered Kisan'} 
                  disabled 
                  style={{ backgroundColor: 'var(--bg-page)', fontWeight: 600 }}
                />
              </div>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>Mobile / Farmer ID</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={`${user?.mobile || '9876500001'} (${user?.user_id || 'F00001'})`} 
                  disabled 
                  style={{ backgroundColor: 'var(--bg-page)', fontWeight: 600 }}
                />
              </div>
            </div>
          </div>

          {/* SECTION 2: PROCUREMENT DETAILS */}
          <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.75rem' }}>
              2. Procurement & Centre Details
            </h3>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>State</label>
                <select 
                  className="form-control"
                  value={selectedState}
                  onChange={(e) => handleStateChange(e.target.value)}
                  style={{ fontWeight: 600 }}
                >
                  <option value="Maharashtra">Maharashtra</option>
                  <option value="Punjab">Punjab</option>
                  <option value="Karnataka">Karnataka</option>
                  <option value="Goa">Goa</option>
                  <option value="Haryana">Haryana</option>
                  <option value="Madhya Pradesh">Madhya Pradesh</option>
                </select>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>Crop to Sell</label>
                <select 
                  className="form-control"
                  value={crop}
                  onChange={(e) => setCrop(e.target.value)}
                  style={{ fontWeight: 600 }}
                >
                  {supportedCropsList.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>Expected Quantity (Quintals)</label>
                <input 
                  type="number" 
                  step="0.5"
                  min="1"
                  className="form-control" 
                  placeholder="e.g. 42"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  required
                  style={{ fontWeight: 600 }}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>Preferred Procurement Centre</label>
                <select 
                  className="form-control"
                  value={selectedCentreId}
                  onChange={(e) => setSelectedCentreId(e.target.value)}
                  style={{ fontWeight: 600 }}
                >
                  {centres
                    .filter(c => !c.state || c.state.toLowerCase() === selectedState.toLowerCase() || centres.length <= 5)
                    .map(c => (
                      <option key={c.centre_id} value={c.centre_id}>
                        {c.centre_name} ({c.centre_id}) — {c.location || c.district || 'Yard'}
                      </option>
                    ))}
                </select>
              </div>

              {/* Recommended Centre Suggestion */}
              {bestRecommendedCentre && (
                <div style={{
                  backgroundColor: 'rgba(27, 77, 62, 0.08)',
                  border: '1px solid var(--primary-border)',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem'
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 800, textTransform: 'uppercase' }}>
                      <Sparkles size={13} /> Recommended Centre
                    </div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
                      {bestRecommendedCentre.centre_name || bestRecommendedCentre.centre_id}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                      Wait: ~{bestRecommendedCentre.estimated_wait_minutes || 20}m • Queue: {bestRecommendedCentre.current_queue || 4} farmers
                    </div>
                  </div>
                  {bestRecommendedCentre.centre_id !== selectedCentreId && (
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => setSelectedCentreId(bestRecommendedCentre.centre_id)}
                      style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                    >
                      Select
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Daily Capacity Status */}
            {dailyCapacityInfo && (
              <div style={{
                marginTop: '1rem',
                backgroundColor: 'var(--bg-page)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '10px 14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '0.5rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', color: 'var(--secondary)', fontWeight: 600 }}>
                  <Scale size={16} style={{ color: 'var(--primary)' }} />
                  <span>Available Capacity for {formatDateDisplay(date)}:</span>
                </div>
                <div style={{ fontSize: '0.9rem', fontWeight: 800, color: dailyCapacityInfo.available_quintals > 0 ? 'var(--primary)' : 'var(--danger)' }}>
                  {dailyCapacityInfo.available_quintals} Quintals Available ({dailyCapacityInfo.booked_quintals} / {dailyCapacityInfo.max_quintals_per_day} Booked)
                </div>
              </div>
            )}
          </div>

          {/* SECTION 3: INTELLIGENT SLOT & DATE */}
          <div style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1.25rem' }}>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.75rem' }}>
              3. Intelligent Slot & Date Window
            </h3>

            {/* Intelligent Slot Suggestion Card */}
            {recommendedSlots.length > 0 && (
              <div style={{
                backgroundColor: 'var(--surface-secondary)',
                border: '1px solid #10b981',
                borderRadius: '10px',
                padding: '14px 18px',
                marginBottom: '1rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '1rem'
              }}>
                <div style={{ flex: 1, minWidth: '240px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#10b981', fontWeight: 800, textTransform: 'uppercase' }}>
                    <Sparkles size={14} /> AI Recommended Slot Window
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
                    {recommendedSlots[0].start_time} - {recommendedSlots[0].end_time} ({formatDateDisplay(date)})
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Farmers ahead: <strong>{recommendedSlots[0].farmers_ahead ?? 0}</strong> • Expected wait: <strong>{recommendedSlots[0].expected_wait_min ?? 15} mins</strong>
                    {recommendedSlots[0].recommended_departure && (
                      <span> • Suggested departure: <strong style={{ color: 'var(--primary)' }}>{recommendedSlots[0].recommended_departure}</strong></span>
                    )}
                  </div>
                  {recommendedSlots[0].reason && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px', fontStyle: 'italic' }}>
                      Why this slot: {recommendedSlots[0].reason}
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '4px 10px', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    Lowest Queue
                  </span>
                  {selectedSlotId !== recommendedSlots[0].slot_id && (
                    <button
                      type="button"
                      onClick={() => {
                        const matchSlot = slots.find(s => s.id === recommendedSlots[0].slot_id || (s.start_time === recommendedSlots[0].start_time && s.end_time === recommendedSlots[0].end_time));
                        if (matchSlot && !matchSlot.is_full) {
                          setSelectedSlotId(matchSlot.id);
                        }
                      }}
                      className="btn btn-sm btn-outline"
                      style={{ fontSize: '0.75rem', padding: '2px 8px' }}
                    >
                      Select Recommended
                    </button>
                  )}
                </div>
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label" style={{ fontWeight: 700 }}>Appointment Date</label>
                <DateInput 
                  id="booking-appointment-date"
                  value={date}
                  onChange={(newVal) => setDate(newVal)}
                  min={todayStr}
                  required
                />
              </div>
            </div>

            {/* Slot selection grid */}
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" style={{ fontWeight: 700 }}>Select Time Window</label>
              
              {loadingSlots ? (
                <p style={{ fontSize: '0.9rem', color: 'var(--muted)', padding: '0.5rem 0' }}>
                  Checking slot capacity and queue status...
                </p>
              ) : slots.length === 0 ? (
                <p style={{ fontSize: '0.9rem', color: 'var(--muted)', padding: '0.5rem 0' }}>
                  No slots configured for this date. Please choose another date.
                </p>
              ) : (
                <>
                  <div className="slot-grid">
                    {slots.map(s => {
                      const isSelected = selectedSlotId === s.id;
                      const isFull = s.is_full;
                      const isRec = s.rank_type === 'RECOMMENDED';
                      const isAlt = s.rank_type === 'ALTERNATIVE';

                      return (
                        <div 
                          key={s.id}
                          className={`slot-card ${isSelected ? 'selected' : ''} ${isFull ? 'disabled' : ''}`}
                          style={{
                            position: 'relative',
                            borderColor: isSelected ? 'var(--primary)' : isRec ? '#10b981' : isAlt ? '#3b82f6' : 'var(--border)'
                          }}
                          onClick={() => {
                            if (!isFull) {
                              setSelectedSlotId(s.id);
                              setError('');
                            }
                          }}
                        >
                          {isRec && (
                            <span style={{
                              position: 'absolute',
                              top: '-8px',
                              right: '8px',
                              backgroundColor: '#10b981',
                              color: '#ffffff',
                              fontSize: '0.65rem',
                              fontWeight: 800,
                              padding: '1px 6px',
                              borderRadius: '8px'
                            }}>
                              ★ RECOMMENDED
                            </span>
                          )}
                          {isAlt && (
                            <span style={{
                              position: 'absolute',
                              top: '-8px',
                              right: '8px',
                              backgroundColor: '#3b82f6',
                              color: '#ffffff',
                              fontSize: '0.65rem',
                              fontWeight: 800,
                              padding: '1px 6px',
                              borderRadius: '8px'
                            }}>
                              OFF-PEAK
                            </span>
                          )}
                          <div className="slot-time" style={{ fontWeight: 800 }}>
                            {s.start_time} - {s.end_time}
                          </div>
                          <div className="slot-capacity" style={{ color: isFull ? 'var(--danger)' : 'var(--primary)', fontWeight: 600 }}>
                            {isFull ? 'FULL' : `${s.remaining_capacity} slots available`}
                          </div>
                          {s.farmers_ahead !== undefined && !isFull && (
                            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                              Ahead: <strong>{s.farmers_ahead}</strong> • Wait: <strong>{s.expected_wait_min}m</strong>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Slot Intelligence Explanation below the grid */}
                  {(() => {
                    const selectedSlotObj = slots.find(s => s.id === selectedSlotId);
                    if (selectedSlotObj?.reason) {
                      return (
                        <div style={{
                          marginTop: '0.75rem',
                          padding: '8px 14px',
                          borderRadius: '8px',
                          backgroundColor: 'var(--surface-secondary)',
                          border: '1px solid var(--border)',
                          fontSize: '0.82rem',
                          color: 'var(--text-primary)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}>
                          <Info size={16} color="var(--primary)" />
                          <span>
                            <strong>Slot Intelligence:</strong> {selectedSlotObj.reason}
                            {selectedSlotObj.recommended_departure && (
                              <span style={{ marginLeft: '6px', color: 'var(--primary)', fontWeight: 700 }}>
                                (Suggested farm departure: {selectedSlotObj.recommended_departure})
                              </span>
                            )}
                          </span>
                        </div>
                      );
                    }
                    return null;
                  })()}
                </>
              )}
            </div>
          </div>

          {/* SECTION 4: MSP + ESTIMATED PROCUREMENT VALUE */}
          {priceInfo && (
            <div style={{
              backgroundColor: 'var(--bg-page)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '1.25rem',
              marginBottom: '1.5rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <TrendingUp size={16} style={{ color: 'var(--primary)' }} />
                  <span style={{ fontWeight: 800, color: 'var(--secondary)', fontSize: '0.95rem' }}>
                    Official MSP & Estimated Procurement Value
                  </span>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>
                  Subject to weighment & quality
                </span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', textAlign: 'center' }}>
                <div style={{ backgroundColor: 'var(--surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                    Official MSP ({crop})
                  </div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '2px' }}>
                    ₹{priceInfo.official_msp?.toLocaleString('en-IN')}
                    <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}> / quintal</span>
                  </div>
                </div>

                <div style={{ backgroundColor: 'var(--primary-light)', padding: '12px', borderRadius: '8px', border: '1px solid var(--primary-border)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 700, textTransform: 'uppercase' }}>
                    Applicable Procurement Rate
                  </div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 900, color: 'var(--primary)', marginTop: '2px' }}>
                    ₹{priceInfo.estimated_price?.toLocaleString('en-IN')}
                    <span style={{ fontSize: '0.75rem', color: 'var(--primary)' }}> / quintal</span>
                  </div>
                </div>

                <div style={{ backgroundColor: 'var(--surface)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                    Estimated Total Value
                  </div>
                  <div style={{ fontSize: '1.35rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '2px' }}>
                    ₹{((parseFloat(quantity) || 42) * (priceInfo.estimated_price || priceInfo.official_msp || 2369)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </div>
                </div>
              </div>

              <p style={{ margin: '0.75rem 0 0 0', fontSize: '0.8rem', color: 'var(--muted)', lineHeight: 1.4 }}>
                * <strong>Notice:</strong> Estimated procurement value = Expected Quantity ({quantity || 42} Q) × Applicable Rate. Final credit amount depends on certified weighment and laboratory quality grading at the procurement centre.
              </p>
            </div>
          )}

          {/* OPTIONAL ADVANCED INFORMATION TOGGLE */}
          <div style={{ marginBottom: '1.5rem' }}>
            <button
              type="button"
              onClick={() => setShowAdvancedInfo(!showAdvancedInfo)}
              className="btn btn-outline btn-sm"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <Info size={14} />
              {showAdvancedInfo ? 'Hide Advanced Logistics Information' : 'Show Advanced Logistics & Alternative Slots'}
            </button>

            {showAdvancedInfo && (
              <div style={{
                marginTop: '0.75rem',
                backgroundColor: 'var(--bg-page)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '1rem',
                fontSize: '0.85rem'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '0.5rem', color: 'var(--secondary)' }}>
                  Alternative Centres & Logistics Estimates:
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
                  {centres.slice(0, 3).map(c => (
                    <div key={c.centre_id} style={{ backgroundColor: 'var(--surface)', padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                      <div style={{ fontWeight: 700 }}>{c.centre_name}</div>
                      <div style={{ color: 'var(--muted)', fontSize: '0.75rem' }}>
                        Distance: ~{c.distance_km || 12} km • Est. Travel: {c.travel_time_min || 25} mins
                      </div>
                      <div style={{ color: 'var(--primary)', fontSize: '0.75rem', fontWeight: 600 }}>
                        Rec. Departure: 45 min before slot
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* SUBMIT BUTTON */}
          <div>
            <button 
              type="submit" 
              className="btn btn-primary btn-lg"
              style={{ width: '100%', padding: '0.85rem', fontSize: '1.1rem', fontWeight: 800 }}
              disabled={!selectedSlotId || (dailyCapacityInfo && dailyCapacityInfo.available_quintals <= 0)}
            >
              Confirm Procurement Booking
            </button>
          </div>
        </form>
      </div>

      {/* CONFIRMATION SUMMARY MODAL */}
      {showSummaryModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.5rem' }}>
              Confirm Procurement Booking
            </h3>
            <p style={{ fontSize: '0.9rem', marginBottom: '1.25rem', color: 'var(--muted)' }}>
              Please verify your appointment details before final token generation:
            </p>

            <div style={{ backgroundColor: 'var(--bg-page)', padding: '1.25rem', borderRadius: '8px', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.95rem' }}>
              <div><strong>Farmer:</strong> {user?.name} ({user?.user_id})</div>
              <div><strong>Crop:</strong> {crop}</div>
              <div><strong>Quantity:</strong> {quantity} Quintals</div>
              <div><strong>Centre:</strong> {currentCentreDetails?.centre_name || selectedCentreId}</div>
              <div><strong>Date:</strong> {formatDateDisplay(date)}</div>
              <div><strong>Time Window:</strong> {currentSlotObj ? `${currentSlotObj.start_time} - ${currentSlotObj.end_time}` : ''}</div>
              {priceInfo && (
                <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px dashed var(--border)' }}>
                  <div><strong>Official MSP:</strong> ₹{priceInfo.official_msp?.toLocaleString('en-IN')} / Q</div>
                  <div><strong>Estimated Value:</strong> ₹{((parseFloat(quantity) || 42) * (priceInfo.estimated_price || priceInfo.official_msp)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                type="button" 
                className="btn btn-outline" 
                style={{ flex: 1, padding: '0.65rem' }}
                onClick={() => setShowSummaryModal(false)}
                disabled={submitting}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                style={{ flex: 1, padding: '0.65rem', fontWeight: 800 }}
                onClick={handleFinalConfirm}
                disabled={submitting}
              >
                {submitting ? 'Booking...' : 'Confirm Procurement Booking'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
