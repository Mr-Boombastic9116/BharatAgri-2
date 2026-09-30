import React, { useEffect, useState } from 'react';
import { getCentres, getSlots, bookSlot, getCentreDetails, getOperatingConfig, getDailyCapacity } from '../services/api';
import { Calendar, Clock, MapPin, Wheat, AlertCircle, ArrowLeft, Scale, CheckCircle2, Info } from 'lucide-react';
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

export default function SlotBookingPage({ user, onBookingSuccess, navigate }) {
  const [centres, setCentres] = useState([]);
  const [selectedCentreId, setSelectedCentreId] = useState('');
  const [currentCentreDetails, setCurrentCentreDetails] = useState(null);

  const todayStr = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(todayStr);

  const [supportedCropsList, setSupportedCropsList] = useState(['Paddy', 'Wheat', 'Maize']);
  const [crop, setCrop] = useState('Paddy');
  const [quantity, setQuantity] = useState('');

  const [slots, setSlots] = useState([]);
  const [selectedSlotId, setSelectedSlotId] = useState(null);

  const [operatingConfig, setOperatingConfig] = useState({ operating_days: [], non_operational_dates: [] });
  const [dailyCapacityInfo, setDailyCapacityInfo] = useState(null);

  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [noticeInfo, setNoticeInfo] = useState(null);

  // Confirmation Modal Summary state
  const [showSummaryModal, setShowSummaryModal] = useState(false);

  // Fetch list of procurement centres
  useEffect(() => {
    getCentres()
      .then(data => {
        setCentres(data);
        if (data.length > 0) {
          setSelectedCentreId(data[0].centre_id);
          setCurrentCentreDetails(data[0]);
        }
      })
      .catch(err => setError('Unable to load procurement centres. Please try again.'));
  }, []);

  // Update current centre details and crop list when selected centre changes
  useEffect(() => {
    if (selectedCentreId) {
      const found = centres.find(c => c.centre_id === selectedCentreId);
      if (found) {
        setCurrentCentreDetails(found);
        if (found.supported_crops) {
          const cropArr = found.supported_crops.split(',').map(c => c.trim());
          setSupportedCropsList(cropArr);
          if (!cropArr.includes(crop)) {
            setCrop(cropArr[0]);
          }
        }
      }
    }
  }, [selectedCentreId, centres]);

  // Fetch slots, operating config, and daily capacity whenever selectedCentreId or date changes
  useEffect(() => {
    if (selectedCentreId && date) {
      setError('');
      setNoticeInfo(null);
      setSelectedSlotId(null);
      setLoadingSlots(true);

      Promise.all([
        getSlots(selectedCentreId, date),
        getOperatingConfig(selectedCentreId),
        getDailyCapacity(selectedCentreId, date)
      ])
        .then(([slotsData, configData, capData]) => {
          setOperatingConfig(configData);
          setDailyCapacityInfo(capData);

          // 1. Check Non-Operational Date Exception (Holiday)
          const holidayMatch = (configData.non_operational_dates || []).find(d => d.date === date);
          if (holidayMatch) {
            setSlots([]);
            setNoticeInfo({ 
              type: 'closed', 
              message: `The procurement centre is not operational on the selected date (${holidayMatch.reason}).` 
            });
            return;
          }

          // 2. Check Weekly Operating Days
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

          // 3. Check Daily Capacity Exhausted
          if (capData && capData.available_quintals <= 0) {
            setSlots(slotsData || []);
            setNoticeInfo({ 
              type: 'capacity_full', 
              message: `Daily quintal capacity has been reached for this date (0 Quintals available).` 
            });
            return;
          }

          // 4. Check No Slots Configured
          if (!slotsData || slotsData.length === 0) {
            setSlots([]);
            setNoticeInfo({ 
              type: 'empty', 
              message: `No time slots have been configured for this date.` 
            });
            return;
          }

          // 5. Check All Slots Full
          if (slotsData.every(s => s.is_full)) {
            setSlots(slotsData);
            setNoticeInfo({ 
              type: 'slots_full', 
              message: `All time slots are currently full for this date.` 
            });
            return;
          }

          setSlots(slotsData);
        })
        .catch(err => {
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
      setError(`Quantity exceeds daily available capacity! Max available for ${formatDateDisplay(date)} is ${dailyCapacityInfo.available_quintals} Quintals (${dailyCapacityInfo.booked_quintals} / ${dailyCapacityInfo.max_quintals_per_day} Quintals already booked).`);
      return;
    }

    setShowSummaryModal(true);
  };

  const handleFinalConfirm = async () => {
    setSubmitting(true);
    setError('');

    try {
      const newBooking = await bookSlot(
        user.user_id,
        selectedCentreId,
        selectedSlotId,
        crop,
        parseFloat(quantity)
      );
      setShowSummaryModal(false);
      onBookingSuccess(newBooking);
    } catch (err) {
      setError(err.message || 'Booking failed.');
      setShowSummaryModal(false);
    } finally {
      setSubmitting(false);
    }
  };

  const currentSlotObj = slots.find(s => s.id === selectedSlotId);

  return (
    <div style={{ maxWidth: '740px', margin: '0 auto' }} className="animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button 
          className="btn btn-outline btn-sm"
          onClick={() => navigate('farmer-dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <h1 style={{ fontSize: '1.75rem', color: 'var(--secondary)' }}>Book Procurement Slot</h1>
      </div>

      {/* Network / Server Error Notice */}
      {error && (
        <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.25rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Differentiated Informational Notice (Closed / No Slots / Capacity Full) */}
      {noticeInfo && (
        <div className="alert alert-warning" style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px', 
          marginBottom: '1.25rem',
          background: noticeInfo.type === 'closed' ? '#fef2f2' : noticeInfo.type === 'capacity_full' ? '#fff7ed' : '#f8fafc',
          borderColor: noticeInfo.type === 'closed' ? '#fca5a5' : noticeInfo.type === 'capacity_full' ? '#ffedd5' : '#e2e8f0',
          color: noticeInfo.type === 'closed' ? '#991b1b' : noticeInfo.type === 'capacity_full' ? '#c2410c' : 'var(--secondary)'
        }}>
          <Info size={20} />
          <span style={{ fontWeight: 600 }}>{noticeInfo.message}</span>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleReviewBooking}>
          {/* Step 1 & Auto-populated Farmer Details */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Farmer Name</label>
              <input 
                type="text" 
                className="form-control" 
                value={user.name} 
                disabled 
              />
            </div>
            <div className="form-group">
              <label className="form-label">Farmer Mobile / ID</label>
              <input 
                type="text" 
                className="form-control" 
                value={user.user_id} 
                disabled 
              />
            </div>
          </div>

          {/* Select Centre & Supported Crops */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Procurement Centre</label>
              <select 
                className="form-control"
                value={selectedCentreId}
                onChange={(e) => setSelectedCentreId(e.target.value)}
              >
                {centres.map(c => (
                  <option key={c.centre_id} value={c.centre_id}>
                    {c.centre_name} ({c.location || 'Procurement Yard'})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Crop Type</label>
              <select 
                className="form-control"
                value={crop}
                onChange={(e) => setCrop(e.target.value)}
              >
                {supportedCropsList.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Date Picker & Quantity */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Appointment Date</label>
              <DateInput 
                id="booking-appointment-date"
                value={date}
                onChange={(newVal) => setDate(newVal)}
                min={todayStr}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Quantity (Quintals)</label>
              <input 
                type="number" 
                step="0.1"
                min="1"
                className="form-control"
                placeholder="e.g. 50"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Daily Quintal Capacity Status Bar */}
          {dailyCapacityInfo && !error && !noticeInfo && (
            <div style={{
              background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
              border: '1px solid #bbf7d0',
              borderRadius: '10px',
              padding: '12px 16px',
              marginBottom: '1.25rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              fontSize: '0.9rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', fontWeight: 600 }}>
                <Scale size={18} />
                <span>Daily Quintal Limit for {formatDateDisplay(date)}:</span>
              </div>
              <div style={{ color: '#14532d', fontWeight: 800 }}>
                {dailyCapacityInfo.booked_quintals} / {dailyCapacityInfo.max_quintals_per_day} Quintals Booked 
                <span style={{ marginLeft: '8px', color: '#16a34a', fontWeight: 600 }}>
                  ({dailyCapacityInfo.available_quintals} Quintals Available)
                </span>
              </div>
            </div>
          )}

          {/* Time Slot Selection Grid */}
          <div className="form-group" style={{ marginTop: '0.75rem' }}>
            <label className="form-label">Select Available Time Slot</label>
            
            {loadingSlots ? (
              <p style={{ fontSize: '0.9rem', color: 'var(--muted)', padding: '0.5rem 0' }}>
                Checking slot availability & capacity...
              </p>
            ) : slots.length === 0 ? (
              <p style={{ fontSize: '0.9rem', color: 'var(--muted)', padding: '0.5rem 0' }}>
                No time slots available for booking on this date.
              </p>
            ) : (
              <div className="slot-grid">
                {slots.map(s => {
                  const isSelected = selectedSlotId === s.id;
                  const isFull = s.is_full;

                  return (
                    <div 
                      key={s.id}
                      className={`slot-card ${isSelected ? 'selected' : ''} ${isFull ? 'disabled' : ''}`}
                      onClick={() => {
                        if (!isFull) {
                          setSelectedSlotId(s.id);
                          setError('');
                        }
                      }}
                    >
                      <div className="slot-time">{s.start_time} - {s.end_time}</div>
                      <div className="slot-capacity" style={{ color: isFull ? 'var(--danger)' : 'var(--success)' }}>
                        {isFull ? 'FULL (0 Slots Left)' : `${s.booked_count} / ${s.max_capacity} Farmers (${s.remaining_capacity} Remaining)`}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div style={{ marginTop: '2rem' }}>
            <button 
              type="submit" 
              className="btn btn-primary btn-lg"
              style={{ width: '100%' }}
              disabled={!selectedSlotId || (dailyCapacityInfo && dailyCapacityInfo.available_quintals <= 0)}
            >
              Confirm Booking & Generate Pass
            </button>
          </div>
        </form>
      </div>

      {/* Confirmation Summary Modal */}
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
          <div className="card" style={{ maxWidth: '500px', width: '100%', padding: '2rem' }}>
            <h3 style={{ fontSize: '1.35rem', color: 'var(--secondary)', marginBottom: '0.5rem' }}>
              Confirm Appointment Summary
            </h3>
            <p style={{ fontSize: '0.9rem', marginBottom: '1.25rem', color: 'var(--muted)' }}>
              Please review your details before final pass generation:
            </p>

            <div style={{ backgroundColor: 'var(--bg-page)', padding: '1rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.95rem' }}>
              <div><strong>Farmer:</strong> {user.name} ({user.user_id})</div>
              <div><strong>Crop:</strong> {crop}</div>
              <div><strong>Quantity:</strong> {quantity} Quintals</div>
              <div><strong>Centre:</strong> {currentCentreDetails ? currentCentreDetails.centre_name : selectedCentreId}</div>
              <div><strong>Location:</strong> {currentCentreDetails ? currentCentreDetails.location : ''}</div>
              <div><strong>Date:</strong> {formatDateDisplay(date)}</div>
              <div><strong>Time Slot:</strong> {currentSlotObj ? `${currentSlotObj.start_time} - ${currentSlotObj.end_time}` : ''}</div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                type="button" 
                className="btn btn-outline" 
                style={{ flex: 1 }}
                onClick={() => setShowSummaryModal(false)}
                disabled={submitting}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                style={{ flex: 1 }}
                onClick={handleFinalConfirm}
                disabled={submitting}
              >
                {submitting ? 'Generating Pass...' : 'Confirm Booking'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
