import React from 'react';
import StatusBadge from './StatusBadge';
import { QRCodeSVG } from 'qrcode.react';
import { Calendar, Clock, MapPin, Wheat, User, Hash, Phone, ShieldCheck } from 'lucide-react';

import { formatDateDisplay } from '../utils/dateUtils';

export default function AppointmentCard({ booking }) {
  if (!booking) return null;

  const qrValue = booking.qr_token || `BA-QR-${booking.appointment_id || booking.booking_id}`;
  const appointmentId = booking.appointment_id || booking.booking_id;

  return (
    <div className="appointment-card" style={{ maxWidth: '560px', margin: '0 auto', padding: '2rem' }}>
      {/* Title */}
      <div className="appointment-header" style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', backgroundColor: 'var(--primary-light)', color: 'var(--primary-hover)', padding: '0.25rem 0.85rem', borderRadius: '9999px', fontSize: '0.8rem', fontWeight: 800, marginBottom: '0.5rem' }}>
          <ShieldCheck size={14} /> OFFICIAL PROCUREMENT PASS
        </div>
        <h2 style={{ color: 'var(--primary)', margin: 0, fontSize: '1.6rem', fontWeight: 800 }}>BHARATAGRI</h2>
      </div>

      {/* QR Code Section */}
      <div style={{
        backgroundColor: '#ffffff',
        border: '2px solid var(--border)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
        textAlign: 'center',
        marginBottom: '1.5rem',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{ display: 'inline-block', padding: '0.75rem', backgroundColor: 'white', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
          <QRCodeSVG 
            value={qrValue} 
            size={160} 
            level="H" 
            includeMargin={true}
          />
        </div>

        <div style={{ marginTop: '0.75rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            APPOINTMENT ID
          </span>
          <div className="appointment-id-badge" style={{ marginTop: '0.25rem' }}>
            {appointmentId}
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="appointment-details" style={{ rowGap: '1.1rem' }}>
        <div className="appointment-item">
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <User size={13} /> Farmer Name
          </label>
          <value>{booking.farmer_name || booking.farmer_id}</value>
        </div>

        <div className="appointment-item">
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Phone size={13} /> Contact Mobile
          </label>
          <value>{booking.farmer_mobile || 'Registered Mobile'}</value>
        </div>

        <div className="appointment-item">
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Wheat size={13} /> Crop & Quantity
          </label>
          <value>{booking.crop} — {booking.quantity} Quintals</value>
        </div>

        <div className="appointment-item">
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <MapPin size={13} /> Procurement Centre
          </label>
          <value>{booking.centre_name || booking.centre_id}</value>
        </div>

        <div className="appointment-item">
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Calendar size={13} /> Date
          </label>
          <value>{formatDateDisplay(booking.date)}</value>
        </div>

        <div className="appointment-item">
          <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={13} /> Time Slot
          </label>
          <value>{booking.time_slot || `${booking.start_time} - ${booking.end_time}`}</value>
        </div>
      </div>

      {/* Status Footer */}
      <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 700 }}>VERIFICATION STATUS:</span>
        <StatusBadge status={booking.status} />
      </div>
    </div>
  );
}
