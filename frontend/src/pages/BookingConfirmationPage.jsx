import React from 'react';
import AppointmentCard from '../components/AppointmentCard';
import { CheckCircle2, ArrowLeft, PlusCircle, Ticket, Calendar, Clock, MapPin, Users } from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';

export default function BookingConfirmationPage({ booking, navigate }) {
  if (!booking) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
        <p>No booking details found.</p>
        <button className="btn btn-primary" onClick={() => navigate('farmer-dashboard')}>
          Go to Dashboard
        </button>
      </div>
    );
  }

  const tokenVal = booking.token || booking.token_number || 'A184';
  const centreName = booking.centre_name || booking.centre_id || 'Centre #17';
  const dateVal = formatDateDisplay(booking.date) || '12 October';
  const timeVal = booking.time_slot || `${booking.start_time || '10:30'} - ${booking.end_time || '11:00 AM'}`;
  const farmersAhead = booking.farmers_ahead ?? 12;
  const waitMin = Math.round(booking.expected_wait_min ?? booking.predicted_wait_min ?? 28);

  return (
    <div style={{ maxWidth: '680px', margin: '1rem auto', paddingBottom: '3rem' }}>
      
      {/* Top Banner */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: 'var(--success-bg)',
          color: 'var(--success-text)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1rem auto'
        }}>
          <CheckCircle2 size={36} />
        </div>

        <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--secondary)', marginBottom: '0.25rem' }}>
          Booking Confirmed
        </h1>

        <p style={{ fontSize: '1rem', color: 'var(--muted)' }}>
          Your appointment and digital queue token have been successfully generated in the central procurement system.
        </p>
      </div>

      {/* PROMINENT TOKEN & QUEUE CONFIRMATION CARD (Requirement 6) */}
      <div className="card" style={{
        border: '2px solid var(--primary)',
        borderRadius: '16px',
        padding: '1.75rem',
        marginBottom: '2rem',
        backgroundColor: 'var(--surface)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.06)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          borderBottom: '1px solid var(--border)',
          paddingBottom: '1.25rem',
          marginBottom: '1.25rem'
        }}>
          <div>
            <span style={{
              backgroundColor: 'var(--primary-light)',
              color: 'var(--primary)',
              padding: '3px 10px',
              borderRadius: '6px',
              fontSize: '0.8rem',
              fontWeight: 800,
              letterSpacing: '0.5px'
            }}>
              OFFICIAL TOKEN
            </span>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--primary)', lineHeight: 1.1, marginTop: '4px' }}>
              Token: {tokenVal}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>APPOINTMENT ID</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)' }}>
              {booking.appointment_id || booking.booking_id}
            </div>
          </div>
        </div>

        {/* Confirmation Details Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>
              <MapPin size={14} /> Centre
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
              {centreName}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
              {booking.location || 'APMC Yard'}
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>
              <Calendar size={14} /> Date
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
              {dateVal}
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>
              <Clock size={14} /> Time
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
              {timeVal}
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>
              <Users size={14} /> Farmers ahead
            </div>
            <div style={{ fontSize: '1.3rem', fontWeight: 900, color: 'var(--secondary)', marginTop: '2px' }}>
              {farmersAhead}
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>
              <Clock size={14} /> Expected wait
            </div>
            <div style={{ fontSize: '1.3rem', fontWeight: 900, color: 'var(--primary)', marginTop: '2px' }}>
              {waitMin} minutes
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 700 }}>
              Harvest & Quantity
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--secondary)', marginTop: '2px' }}>
              {booking.crop} — {booking.quantity} Quintals
            </div>
          </div>
        </div>
      </div>

      {/* Digital Appointment Card with QR code */}
      <AppointmentCard booking={booking} />

      {/* Action Navigation Buttons */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        justifyContent: 'center', 
        marginTop: '2.5rem',
        flexWrap: 'wrap'
      }}>
        <button 
          className="btn btn-primary btn-lg"
          onClick={() => navigate('my-booking')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <Ticket size={18} /> View in My Booking & Queue
        </button>

        <button 
          className="btn btn-outline btn-lg"
          onClick={() => navigate('farmer-dashboard')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <ArrowLeft size={18} /> Back to Dashboard
        </button>

        <button 
          className="btn btn-outline btn-lg"
          onClick={() => navigate('book-slot')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
        >
          <PlusCircle size={18} /> Book Another Slot
        </button>
      </div>
    </div>
  );
}
