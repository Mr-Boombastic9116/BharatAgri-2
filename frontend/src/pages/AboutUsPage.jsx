import React from 'react';
import { 
  Info, 
  User, 
  Calendar, 
  Clock, 
  Scale, 
  QrCode, 
  Building2, 
  Cpu, 
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function AboutUsPage({ navigate }) {
  return (
    <div className="about-us-page animate-fade-in" style={{ padding: '24px 0', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Header Banner */}
      <div className="card shadow-sm mb-4" style={{
        background: 'linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%)',
        color: 'white',
        borderRadius: '16px',
        padding: '36px 28px'
      }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
          <span style={{ 
            background: 'rgba(255, 255, 255, 0.18)', 
            padding: '6px 16px', 
            borderRadius: '20px', 
            fontSize: '0.85rem',
            fontWeight: 600,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Info size={16} /> About BHARATAGRI
          </span>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 800, marginTop: '16px', marginBottom: '12px' }}>
            Agricultural Procurement Scheduling System
          </h1>
          <p style={{ fontSize: '1.05rem', opacity: 0.9, lineHeight: '1.6', margin: 0 }}>
            An advanced agricultural platform developed to help farmers schedule grain delivery dates and enable procurement centres to manage daily intake capacity without physical queues.
          </p>
        </div>
      </div>

      {/* Section 1: What is BHARATAGRI & Problem Statement */}
      <div className="grid grid-2 mb-4" style={{ gap: '24px' }}>
        <div className="card shadow-sm" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'var(--info-bg)', color: 'var(--info-text)', width: '42px', height: '42px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Info size={22} />
            </div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>What is BHARATAGRI?</h2>
          </div>
          <p style={{ color: 'var(--muted)', lineHeight: '1.6', margin: 0, fontSize: '0.95rem' }}>
            BHARATAGRI is a web-based slot booking and scheduling platform for agricultural procurement. It allows farmers to reserve a specific date and time slot to deliver their harvested crops to nearby government procurement centres.
          </p>
        </div>

        <div className="card shadow-sm" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'var(--warning-bg)', color: 'var(--warning-text)', width: '42px', height: '42px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertCircle size={22} />
            </div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>What problem does it address?</h2>
          </div>
          <p style={{ color: 'var(--muted)', lineHeight: '1.6', margin: 0, fontSize: '0.95rem' }}>
            During peak harvest seasons, procurement centres experience unpredictable overcrowding. Farmers often wait in long queues for days without knowing if the centre has daily capacity remaining to process their grain.
          </p>
        </div>
      </div>

      {/* Section 2: Implemented Features */}
      <div className="card shadow-sm mb-4" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ background: 'var(--success-bg)', color: 'var(--success-text)', width: '42px', height: '42px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CheckCircle2 size={22} />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>What does it provide?</h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: '2px 0 0 0' }}>Implemented system features</p>
          </div>
        </div>

        <div className="grid grid-3" style={{ gap: '20px' }}>
          <div style={{ background: 'var(--bg-page)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--primary)' }}>
              <User size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>Farmer Appointment Booking</h3>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: 0, lineHeight: '1.5' }}>
              Farmers can log in, select a crop type, specify crop quantity in Quintals, and book an appointment.
            </p>
          </div>

          <div style={{ background: 'var(--bg-page)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--primary)' }}>
              <Calendar size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>Date-wise Slot Availability</h3>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: 0, lineHeight: '1.5' }}>
              View operational days and dates when the procurement centre is open for crop intake.
            </p>
          </div>

          <div style={{ background: 'var(--bg-page)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--primary)' }}>
              <Scale size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>Daily Quintal Capacity</h3>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: 0, lineHeight: '1.5' }}>
              Limits total daily grain intake per centre to prevent processing bottlenecks.
            </p>
          </div>

          <div style={{ background: 'var(--bg-page)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--primary)' }}>
              <Clock size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>Time-slot Capacity</h3>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: 0, lineHeight: '1.5' }}>
              Enforces maximum farmer limits per time slot so arrivals are evenly distributed.
            </p>
          </div>

          <div style={{ background: 'var(--bg-page)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--primary)' }}>
              <QrCode size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>QR-Based Verification</h3>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: 0, lineHeight: '1.5' }}>
              Generates a digital pass with a QR code that procurement staff can scan to verify appointments.
            </p>
          </div>

          <div style={{ background: 'var(--bg-page)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', color: 'var(--primary)' }}>
              <Building2 size={20} />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>Procurement-Centre Scheduling</h3>
            </div>
            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: 0, lineHeight: '1.5' }}>
              Procurement staff can set weekly operating days, define holiday dates, and manage daily capacity limits.
            </p>
          </div>
        </div>
      </div>

      {/* Section 3: Technology Stack */}
      <div className="card shadow-sm mb-4" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <div style={{ background: 'rgba(124, 58, 237, 0.15)', color: '#a855f7', width: '42px', height: '42px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={22} />
          </div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0, color: 'var(--secondary)' }}>Technology Stack</h2>
        </div>
        <p style={{ color: 'var(--muted)', lineHeight: '1.6', margin: '0 0 16px 0', fontSize: '0.95rem' }}>
          Built with a robust, enterprise-grade architecture:
        </p>
        <ul style={{ paddingLeft: '20px', color: 'var(--muted)', lineHeight: '1.8', margin: 0, fontSize: '0.925rem' }}>
          <li><strong style={{ color: 'var(--secondary)' }}>Frontend:</strong> React with Vite, Lucide Icons, and Recharts analytics library.</li>
          <li><strong style={{ color: 'var(--secondary)' }}>Backend:</strong> Python FastAPI REST API with SQLAlchemy ORM.</li>
          <li><strong style={{ color: 'var(--secondary)' }}>Database:</strong> MySQL relational database storing appointments, centres, capacity configs, and audit logs.</li>
        </ul>
      </div>

      {/* Navigation Footer */}
      <div className="card shadow-sm" style={{ padding: '28px', textAlign: 'center', background: 'var(--bg-page)', border: '1px solid var(--border)' }}>
        <h3 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '8px', color: 'var(--secondary)' }}>
          Explore BHARATAGRI
        </h3>
        <p style={{ color: 'var(--muted)', marginBottom: '20px', fontSize: '0.925rem' }}>
          Access farmer booking or procurement centre portal.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={() => navigate('login', { role: 'farmer' })}>
            Farmer Login / Register
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('login', { role: 'centre' })}>
            Centre Login / Register
          </button>
        </div>
      </div>
    </div>
  );
}
