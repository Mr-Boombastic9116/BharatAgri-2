import React, { useEffect, useState, useCallback } from 'react';
import { getFarmerBookings, getFarmerOverview, trackToken, getLiveQueue } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import AppointmentCard from '../components/AppointmentCard';
import {
  Ticket, Calendar, Clock, MapPin, Users, IndianRupee,
  CheckCircle2, AlertCircle, ArrowLeft, RefreshCw, QrCode,
  FileText, ShieldCheck, ExternalLink, ChevronRight, Bell, HelpCircle,
  ChevronDown, ChevronUp, Scale, Info
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';

export default function MyBookingPage({ user, navigate }) {
  const farmerIdentifier = user?.user_id;

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [activeBooking, setActiveBooking] = useState(null);
  const [queueLive, setQueueLive] = useState(null);
  const [overview, setOverview] = useState(null);
  const [showPassModal, setShowPassModal] = useState(false);
  const [error, setError] = useState(null);
  const [expandedBookingId, setExpandedBookingId] = useState(null);

  const loadBookingData = useCallback(async () => {
    if (!farmerIdentifier) return;
    setLoading(true);
    setError(null);
    try {
      const [bookingsList, overviewData] = await Promise.all([
        getFarmerBookings(farmerIdentifier).catch(() => []),
        getFarmerOverview(farmerIdentifier).catch(() => null)
      ]);

      const list = Array.isArray(bookingsList) ? bookingsList : [];
      setBookings(list);
      setOverview(overviewData);

      // Find the most recent active / upcoming booking
      const active = list.find(b => !['COMPLETED', 'CANCELLED', 'REJECTED', 'EXPIRED'].includes(b.status)) || list[0] || null;
      setActiveBooking(active);

      // Track live queue for active booking if token exists
      if (active) {
        const tokenVal = active.token || active.token_number || active.appointment_id;
        if (tokenVal) {
          try {
            const tokenTrack = await trackToken(tokenVal);
            setQueueLive(tokenTrack);
          } catch {
            if (active.centre_id) {
              const live = await getLiveQueue(active.centre_id).catch(() => null);
              if (live) setQueueLive(live);
            }
          }
        }
      }
    } catch (err) {
      console.error('Failed to load my booking:', err);
      setError('Unable to load booking records. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [farmerIdentifier]);

  useEffect(() => {
    loadBookingData();
  }, [loadBookingData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadBookingData();
    setRefreshing(false);
  };

  // Queue metrics resolution
  const tokenNumber = activeBooking?.token || activeBooking?.token_number || overview?.token_tracking?.token_number || 'A184';
  const farmersAhead = queueLive?.farmers_ahead ?? activeBooking?.farmers_ahead ?? overview?.token_tracking?.farmers_ahead ?? 0;
  const currentServingToken = queueLive?.currently_serving_token ?? queueLive?.current_token ?? (activeBooking ? `A${Math.max(1, (parseInt(String(tokenNumber).replace(/\D/g, '')) || 184) - farmersAhead)}` : 'A177');
  const waitMin = queueLive?.estimated_waiting_time_minutes ?? queueLive?.predicted_wait_min ?? activeBooking?.estimated_wait_min ?? 15;
  const centreStatus = queueLive?.centre_status || queueLive?.status_label || 'Centre operating normally';
  const departureTime = queueLive?.recommended_departure_time || '1 hour before slot';
  const comeNowActive = queueLive?.come_now_alert || (farmersAhead <= 5 && farmersAhead >= 0 && activeBooking?.status !== 'COMPLETED');

  return (
    <div style={{ maxWidth: '820px', margin: '0 auto', paddingBottom: '3rem' }}>
      
      {/* Top Header & Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={() => navigate('farmer-dashboard')}
            className="btn btn-outline"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '0.45rem 0.85rem' }}
          >
            <ArrowLeft size={16} /> Dashboard
          </button>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
              My Booking & Token
            </h1>
            <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--muted)' }}>
              Live appointment status, dynamic token queue, and pass details
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn btn-outline"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '0.45rem 0.85rem' }}
          >
            <RefreshCw size={14} className={refreshing ? 'spin' : ''} />
            {refreshing ? 'Updating...' : 'Refresh'}
          </button>
          <button
            onClick={() => navigate('book-slot')}
            className="btn btn-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '0.45rem 1rem' }}
          >
            <Calendar size={16} /> Book New Slot
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.25rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--muted)' }}>
          <RefreshCw size={32} className="spin" style={{ margin: '0 auto 1rem auto', color: 'var(--primary)' }} />
          <p style={{ margin: 0, fontWeight: 600 }}>Loading your booking and token queue...</p>
        </div>
      ) : activeBooking ? (
        <>
          {/* Dynamic "COME NOW" Alert Banner */}
          {comeNowActive && (
            <div style={{
              backgroundColor: 'var(--danger-bg)',
              border: '2px solid var(--danger)',
              borderRadius: '12px',
              padding: '1.25rem 1.5rem',
              marginBottom: '1.5rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '1rem',
              boxShadow: '0 4px 12px rgba(239, 68, 68, 0.15)'
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
                    backgroundColor: 'var(--danger)',
                    color: '#ffffff',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    textTransform: 'uppercase'
                  }}>
                    Urgent Advisory
                  </span>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#991b1b' }}>
                    Your Turn Is Approaching
                  </h3>
                </div>
                <p style={{ margin: '0.5rem 0 0 0', fontSize: '1.05rem', fontWeight: 700, color: '#7f1d1d', lineHeight: 1.5 }}>
                  Only {farmersAhead} {farmersAhead === 1 ? 'farmer' : 'farmers'} ahead of you in line.
                  Please proceed immediately to {activeBooking.centre_name || activeBooking.centre_id}.
                </p>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem', color: '#b91c1c' }}>
                  Estimated waiting time is under {Math.round(waitMin)} minutes. Keep your vehicle and crop ready for weighment.
                </p>
              </div>
            </div>
          )}

          {/* ACTIVE BOOKING CARD */}
          <div className="card" style={{
            border: '2px solid var(--primary)',
            borderRadius: '16px',
            padding: '1.75rem',
            marginBottom: '2rem',
            boxShadow: '0 4px 16px rgba(0,0,0,0.06)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1.25rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.35rem' }}>
                  <span style={{
                    backgroundColor: 'rgba(27, 77, 62, 0.12)',
                    color: 'var(--primary)',
                    padding: '3px 10px',
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    fontWeight: 800,
                    letterSpacing: '0.5px'
                  }}>
                    ACTIVE BOOKING
                  </span>
                  <StatusBadge status={activeBooking.status} />
                </div>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                  Booking ID: {activeBooking.appointment_id || activeBooking.booking_id}
                </h2>
              </div>

              {/* Digital Token Badge */}
              <div style={{
                textAlign: 'center',
                backgroundColor: 'var(--bg-page)',
                border: '2px solid var(--primary)',
                borderRadius: '12px',
                padding: '0.75rem 1.5rem',
                minWidth: '140px'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                  Your Token
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--primary)', lineHeight: 1.1, marginTop: '2px' }}>
                  {tokenNumber}
                </div>
              </div>
            </div>

            {/* LIVE QUEUE & STATUS TILES */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '1rem',
              backgroundColor: 'var(--bg-page)',
              border: '1px solid var(--border)',
              borderRadius: '12px',
              padding: '1.25rem',
              marginBottom: '1.5rem'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                  <Users size={14} /> Farmers Ahead
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 900, color: farmersAhead <= 5 ? 'var(--danger)' : 'var(--secondary)', marginTop: '4px' }}>
                  {farmersAhead}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
                  Serving now: <strong>{currentServingToken}</strong>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                  <Clock size={14} /> Estimated Wait
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '4px' }}>
                  {Math.round(waitMin)} min
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
                  ML queue prediction
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                  <CheckCircle2 size={14} /> Centre Status
                </div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--success)', marginTop: '6px' }}>
                  {centreStatus}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
                  Gates operational
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase' }}>
                  <Calendar size={14} /> Departure Plan
                </div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--primary)', marginTop: '6px' }}>
                  {departureTime}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '2px' }}>
                  Avoid gate congestion
                </div>
              </div>
            </div>

            {/* DETAILS GRID */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '1.25rem',
              marginBottom: '1.5rem'
            }}>
              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Crop & Quantity</div>
                <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
                  {activeBooking.crop} — {activeBooking.quantity} Quintals
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Procurement Centre</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
                  {activeBooking.centre_name || activeBooking.centre_id}
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                  {activeBooking.location || 'Official APMC Yard'}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Appointment Date & Slot</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
                  {formatDateDisplay(activeBooking.date)}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                  {activeBooking.time_slot || `${activeBooking.start_time} - ${activeBooking.end_time}`}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>Disbursement & Payment Status</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: activeBooking.payment_status === 'PAID' ? 'var(--success)' : 'var(--warning)', marginTop: '2px' }}>
                  {activeBooking.payment_status || 'PENDING'}
                  {activeBooking.payment_amount ? ` (₹${Number(activeBooking.payment_amount).toLocaleString('en-IN')})` : ''}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                  {activeBooking.payment_status === 'PAID'
                    ? `Ref: ${activeBooking.dbt_reference || 'DBT Direct Credit'}`
                    : 'Calculated upon weighment and gate inspection'}
                </div>
              </div>
            </div>

            {/* ACTION BUTTONS */}
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', borderTop: '1px solid var(--border)', paddingTop: '1.25rem' }}>
              <button
                onClick={() => setShowPassModal(true)}
                className="btn btn-primary"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.65rem 1.25rem', fontSize: '0.95rem' }}
              >
                <QrCode size={18} /> View Official Gate Pass
              </button>
              <button
                onClick={handleRefresh}
                className="btn btn-outline"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.65rem 1.25rem' }}
              >
                <RefreshCw size={16} /> Refresh Queue Info
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', marginBottom: '2rem' }}>
          <Ticket size={48} style={{ color: 'var(--muted)', margin: '0 auto 1rem auto' }} />
          <h2 style={{ fontSize: '1.5rem', color: 'var(--secondary)', marginBottom: '0.5rem' }}>
            No Active Bookings Found
          </h2>
          <p style={{ color: 'var(--muted)', maxWidth: '420px', margin: '0 auto 1.5rem auto' }}>
            You do not currently have any active procurement appointments scheduled. Book a slot to sell your harvest directly at official MSP rates.
          </p>
          <button
            onClick={() => navigate('book-slot')}
            className="btn btn-primary btn-lg"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            <Calendar size={18} /> Book Procurement Slot Now
          </button>
        </div>
      )}

      {/* BOOKING HISTORY SECTION */}
      <div style={{ marginTop: '2.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={20} style={{ color: 'var(--primary)' }} />
            Booking History ({bookings.length})
          </h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
            All past and scheduled procurement appointments
          </span>
        </div>

        {bookings.length === 0 ? (
          <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--muted)' }}>
            No historical bookings on record.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {bookings.map((b, idx) => {
              const itemKey = b.appointment_id || b.id || idx;
              const isExpanded = expandedBookingId === itemKey;

              return (
                <div
                  key={itemKey}
                  className="card"
                  style={{
                    padding: '1.25rem',
                    border: isExpanded ? '2px solid var(--primary)' : '1px solid var(--border)',
                    borderRadius: '12px',
                    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
                    boxShadow: isExpanded ? '0 4px 16px rgba(0,0,0,0.06)' : 'none'
                  }}
                >
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    flexWrap: 'wrap',
                    gap: '1rem'
                  }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 800, color: 'var(--secondary)', fontSize: '1.05rem' }}>
                          {b.appointment_id || `Booking #${b.id}`}
                        </span>
                        <span style={{
                          backgroundColor: 'var(--bg-page)',
                          border: '1px solid var(--border)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 800,
                          color: 'var(--primary)'
                        }}>
                          Token {b.token || b.token_number || '-'}
                        </span>
                        <StatusBadge status={b.status} />
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                        <strong>{b.crop}</strong> • {b.quantity} Q • {b.centre_name || b.centre_id} • {formatDateDisplay(b.date)} ({b.time_slot || b.start_time || 'Slot'})
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 600 }}>Payment Status</div>
                        <div style={{
                          fontSize: '0.95rem',
                          fontWeight: 800,
                          color: b.payment_status === 'PAID' ? 'var(--success)' : 'var(--muted)'
                        }}>
                          {b.payment_status || 'PENDING'}
                          {b.payment_amount ? ` (₹${Number(b.payment_amount).toLocaleString('en-IN')})` : ''}
                        </div>
                      </div>

                      <button
                        onClick={() => setExpandedBookingId(isExpanded ? null : itemKey)}
                        className="btn btn-outline btn-sm"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 14px',
                          fontWeight: 700,
                          fontSize: '0.82rem'
                        }}
                      >
                        {isExpanded ? 'Hide Details' : 'View Details'}
                        {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                      </button>
                    </div>
                  </div>

                  {/* EXPANDABLE DETAILS DISCLOSURE */}
                  {isExpanded && (
                    <div style={{
                      marginTop: '1.25rem',
                      paddingTop: '1.25rem',
                      borderTop: '1px solid var(--border)',
                      backgroundColor: 'var(--bg-page)',
                      borderRadius: '8px',
                      padding: '1.25rem'
                    }}>
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '1.25rem',
                        marginBottom: '1.25rem'
                      }}>
                        {/* Block 1: Centre & Slot */}
                        <div>
                          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--muted)', fontWeight: 800, marginBottom: '6px' }}>
                            Centre & Slot Details
                          </div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--secondary)' }}>
                            {b.centre_name || b.centre_id}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Location: {b.location || b.district || 'Official State APMC Yard'}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Slot: {b.time_slot || `${b.start_time || '09:00 AM'} - ${b.end_time || '11:00 AM'}`}
                          </div>
                          {b.redirected_from_centre_id && (
                            <div style={{ fontSize: '0.78rem', color: 'var(--warning-text)', marginTop: '4px', fontWeight: 600 }}>
                              Redirected from {b.redirected_from_centre_id} ({b.redirection_reason || 'Capacity balancing'})
                            </div>
                          )}
                        </div>

                        {/* Block 2: Commodity & Volume */}
                        <div>
                          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--muted)', fontWeight: 800, marginBottom: '6px' }}>
                            Produce & Volume
                          </div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--secondary)' }}>
                            {b.crop}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Booked Volume: <strong>{b.quantity} Quintals</strong>
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Weighed Volume: {b.net_weight_quintals ? <strong>{b.net_weight_quintals} Q</strong> : (b.status === 'COMPLETED' ? 'Certified upon weighment' : 'Pending Weighment')}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Lot Tracking: {b.lot_id || `LOT-${(b.appointment_id || '').slice(-6)}`}
                          </div>
                        </div>

                        {/* Block 3: Payment & MSP */}
                        <div>
                          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--muted)', fontWeight: 800, marginBottom: '6px' }}>
                            Financial & Payout
                          </div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: b.payment_status === 'PAID' ? 'var(--success)' : 'var(--secondary)' }}>
                            {b.payment_status || 'PENDING'}
                            {b.payment_amount ? ` • ₹${Number(b.payment_amount).toLocaleString('en-IN')}` : ''}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Rate: ₹{b.rate_per_quintal || b.msp_rate || '5,400'}/Quintal
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Disbursement: {b.dbt_reference ? `Ref: ${b.dbt_reference}` : 'Direct Bank Transfer (Aadhaar Seeded)'}
                          </div>
                        </div>

                        {/* Block 4: Audit & Verification */}
                        <div>
                          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--muted)', fontWeight: 800, marginBottom: '6px' }}>
                            Gate Security & Audit
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                            QR Token: <code style={{ fontSize: '0.75rem', backgroundColor: 'var(--surface-secondary)', padding: '2px 6px', borderRadius: '4px' }}>{b.qr_token || `BA-QR-${b.appointment_id}`}</code>
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '4px' }}>
                            Created: {b.created_at ? formatDateDisplay(b.created_at) : 'Registered Online'}
                          </div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--muted)', marginTop: '2px' }}>
                            Gate Status: {b.verified_at ? `Verified on ${formatDateDisplay(b.verified_at)}` : (b.status === 'COMPLETED' ? 'Completed & Archival Recorded' : 'Ready for Gate Scan')}
                          </div>
                        </div>
                      </div>

                      {/* Disclosure Actions */}
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        flexWrap: 'wrap',
                        gap: '0.75rem',
                        paddingTop: '0.75rem',
                        borderTop: '1px solid var(--border)'
                      }}>
                        <div style={{ fontSize: '0.8rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <ShieldCheck size={14} color="var(--primary)" />
                          Official MSP Procurement Pass recognized across State Mandi Gates.
                        </div>

                        <button
                          onClick={() => {
                            setActiveBooking(b);
                            setShowPassModal(true);
                          }}
                          className="btn btn-primary btn-sm"
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            fontSize: '0.82rem',
                            padding: '6px 14px'
                          }}
                        >
                          <QrCode size={14} /> Open Digital Gate Pass
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* MODAL: Digital Appointment Gate Pass */}
      {showPassModal && activeBooking && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div style={{ maxWidth: '580px', width: '100%', position: 'relative' }}>
            <AppointmentCard booking={activeBooking} />
            <div style={{ textAlign: 'center', marginTop: '1rem' }}>
              <button
                onClick={() => setShowPassModal(false)}
                className="btn btn-outline"
                style={{ backgroundColor: 'var(--surface)', fontWeight: 700 }}
              >
                Close Pass
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
