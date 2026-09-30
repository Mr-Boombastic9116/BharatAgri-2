import React, { useEffect, useState } from 'react';
import { getStats } from '../services/api';
import { Users, Building2, CalendarCheck, ShieldCheck, ArrowRight, Sprout } from 'lucide-react';

export default function HomePage({ navigate }) {
  const [stats, setStats] = useState({
    farmers_registered: '2500+',
    procurement_centres: '120+',
    slots_managed: '5000+'
  });

  useEffect(() => {
    getStats()
      .then(data => {
        setStats({
          farmers_registered: `${data.farmers_registered}+`,
          procurement_centres: `${data.procurement_centres}+`,
          slots_managed: `${data.slots_managed}+`
        });
      })
      .catch(err => console.log('Using default stats fallback'));
  }, []);

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section style={{ 
        backgroundColor: '#ffffff', 
        borderBottom: '1px solid var(--border)',
        padding: '4rem 0 3.5rem 0',
        textAlign: 'center'
      }}>
        <div className="container" style={{ maxWidth: '800px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary-hover)',
            padding: '0.35rem 1rem',
            borderRadius: '9999px',
            fontSize: '0.875rem',
            fontWeight: 700,
            marginBottom: '1.25rem',
            border: '1px solid var(--primary-border)'
          }}>
            <Sprout size={16} /> Official Procurement Portal Prototype
          </div>

          <h1 style={{ 
            fontSize: '2.75rem', 
            fontWeight: 800, 
            letterSpacing: '-1px',
            marginBottom: '1rem',
            color: 'var(--secondary)'
          }}>
            Smart Procurement. Better Farming.
          </h1>

          <p style={{ 
            fontSize: '1.2rem', 
            color: 'var(--muted)', 
            marginBottom: '2rem',
            lineHeight: 1.5
          }}>
            Making agricultural procurement simpler, faster and more transparent for farmers.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button 
              className="btn btn-primary btn-lg"
              onClick={() => navigate('login', { role: 'farmer' })}
            >
              Farmer Login <ArrowRight size={18} />
            </button>
            <button 
              className="btn btn-outline btn-lg"
              onClick={() => navigate('login', { role: 'centre' })}
            >
              Procurement Centre Login
            </button>
          </div>
        </div>
      </section>

      {/* Platform Overview Section */}
      <section style={{ padding: '3.5rem 0', backgroundColor: 'var(--bg-page)' }}>
        <div className="container" style={{ maxWidth: '900px', textAlign: 'center' }}>
          <div className="card" style={{ padding: '2.5rem', border: '1px solid var(--border)' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              backgroundColor: 'var(--primary-light)',
              color: 'var(--primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem auto'
            }}>
              <ShieldCheck size={30} />
            </div>

            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.75rem' }}>About BharatAgri</h2>
            
            <p style={{ fontSize: '1.1rem', color: 'var(--secondary-light)', lineHeight: 1.6 }}>
              One platform connecting farmers with procurement centres for simple slot booking and transparent procurement management.
            </p>
          </div>
        </div>
      </section>

      {/* Statistics Section */}
      <section style={{ padding: '2rem 0 4rem 0' }}>
        <div className="container">
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h2 style={{ fontSize: '1.5rem', color: 'var(--secondary)' }}>Platform Overview</h2>
            <p style={{ fontSize: '0.95rem' }}>Real-time procurement operational metrics</p>
          </div>

          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">
                <Users size={24} />
              </div>
              <div>
                <div className="stat-value">{stats.farmers_registered}</div>
                <div className="stat-label">Farmers Registered</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <Building2 size={24} />
              </div>
              <div>
                <div className="stat-value">{stats.procurement_centres}</div>
                <div className="stat-label">Procurement Centres</div>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-icon">
                <CalendarCheck size={24} />
              </div>
              <div>
                <div className="stat-value">{stats.slots_managed}</div>
                <div className="stat-label">Slots Managed</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
