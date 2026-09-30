import React from 'react';
import AppointmentCard from '../components/AppointmentCard';
import { CheckCircle2, ArrowLeft, PlusCircle } from 'lucide-react';

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

  return (
    <div style={{ maxWidth: '650px', margin: '1rem auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          backgroundColor: 'var(--success-bg)',
          color: 'var(--success)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 1rem auto'
        }}>
          <CheckCircle2 size={36} />
        </div>

        <h1 style={{ fontSize: '2rem', color: 'var(--secondary)', marginBottom: '0.25rem' }}>
          Slot Booked Successfully!
        </h1>

        <p style={{ fontSize: '1rem', color: 'var(--muted)' }}>
          Your appointment at the procurement centre has been confirmed.
        </p>
      </div>

      {/* Digital Appointment Card */}
      <AppointmentCard booking={booking} />

      {/* Action Buttons */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        justifyContent: 'center', 
        marginTop: '2.5rem',
        flexWrap: 'wrap'
      }}>
        <button 
          className="btn btn-primary btn-lg"
          onClick={() => navigate('farmer-dashboard')}
        >
          <ArrowLeft size={18} /> Back to Dashboard
        </button>

        <button 
          className="btn btn-outline btn-lg"
          onClick={() => navigate('book-slot')}
        >
          <PlusCircle size={18} /> Book Another Slot
        </button>
      </div>
    </div>
  );
}
