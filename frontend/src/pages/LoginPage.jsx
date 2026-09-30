import React, { useState } from 'react';
import { loginUser, registerFarmer, registerCentre } from '../services/api';
import { LogIn, UserCheck, Building2, User, AlertCircle, ShieldCheck, Users, Briefcase } from 'lucide-react';
import { useTranslation } from '../context/LanguageContext';

const DEMO_ACCOUNTS = {
  farmer: { email: 'farmer@bharatagri.demo', password: 'BharatAgri@2026', role: 'FARMER' },
  agent: { email: 'agent@bharatagri.demo', password: 'BharatAgri@2026', role: 'AGENT' },
  centre: { email: 'centre@bharatagri.demo', password: 'BharatAgri@2026', role: 'PROCUREMENT_CENTRE' },
  government: { email: 'admin@bharatagri.demo', password: 'BharatAgri@2026', role: 'GOVERNMENT' }
};

export default function LoginPage({ initialRole = 'farmer', onLoginSuccess, navigate }) {
  const { t } = useTranslation();
  const [role, setRole] = useState(initialRole.toLowerCase());
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');

  // Registration State
  const [isRegistering, setIsRegistering] = useState(false);
  const [regName, setRegName] = useState('');
  const [regMobile, setRegMobile] = useState('');
  const [regVillage, setRegVillage] = useState('Ponda');
  const [regId, setRegId] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regLanguage, setRegLanguage] = useState('English');

  // Centre Register State
  const [regLocation, setRegLocation] = useState('Ponda, Goa');
  const [regContact, setRegContact] = useState('9876543210');
  const [regOperatingDays, setRegOperatingDays] = useState('Monday,Tuesday,Wednesday,Thursday,Friday,Saturday');
  const [regOpeningTime, setRegOpeningTime] = useState('09:00 AM');
  const [regClosingTime, setRegClosingTime] = useState('05:00 PM');
  const [regCrops, setRegCrops] = useState('Paddy,Wheat,Maize,Cotton');

  // Error & Loading States
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleQuickFill = (roleKey) => {
    const creds = DEMO_ACCOUNTS[roleKey];
    if (creds) {
      setRole(roleKey);
      setUserId(creds.email);
      setPassword(creds.password);
      setError('');
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!userId.trim() || !password.trim()) {
      setError('Please enter both User ID and Password.');
      return;
    }

    setLoading(true);
    try {
      const user = await loginUser(userId.trim(), password, role.toUpperCase());
      onLoginSuccess(user);
    } catch (err) {
      setError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (!regName.trim() || !regId.trim() || !regPassword.trim()) {
      setError('Please fill in all mandatory fields.');
      return;
    }

    setLoading(true);
    try {
      let registeredUser;
      if (role === 'farmer') {
        if (!regMobile.trim() || !regVillage.trim()) {
          setError('Mobile number and Village are required for Farmer registration.');
          setLoading(false);
          return;
        }
        registeredUser = await registerFarmer(
          regName.trim(),
          regMobile.trim(),
          regVillage.trim(),
          regId.trim(),
          regPassword,
          regLanguage
        );
      } else if (role === 'centre') {
        registeredUser = await registerCentre(
          regName.trim(),
          regId.trim(),
          regPassword,
          regLocation.trim(),
          regContact.trim(),
          regOperatingDays,
          regOpeningTime,
          regClosingTime,
          regCrops
        );
      }
      onLoginSuccess(registeredUser);
    } catch (err) {
      setError(err.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '640px', margin: '1rem auto' }}>
      <div className="card" style={{ padding: '2rem' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '52px', height: '52px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', marginBottom: '0.75rem' }}>
            <ShieldCheck size={28} />
          </div>
          <h2 style={{ fontSize: '1.6rem', color: 'var(--secondary)' }}>
            {isRegistering ? `Create ${role === 'farmer' ? 'Farmer' : 'Centre'} Account` : t('login_title')}
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
            {t('app_tagline')}
          </p>
        </div>

        {/* 4 Roles Selector */}
        {!isRegistering && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '1.5rem' }}>
            {[
              { id: 'farmer', label: t('farmer'), icon: User },
              { id: 'agent', label: t('agent'), icon: Users },
              { id: 'centre', label: 'Centre', icon: Building2 },
              { id: 'government', label: 'Govt', icon: Briefcase }
            ].map((r) => {
              const Icon = r.icon;
              const isSelected = role === r.id;
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => {
                    setRole(r.id);
                    setError('');
                  }}
                  style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem',
                    padding: '0.65rem 0.25rem', borderRadius: 'var(--radius-sm)',
                    border: isSelected ? '2px solid var(--primary)' : '1px solid var(--border)',
                    backgroundColor: isSelected ? 'var(--primary-light)' : 'var(--bg-page)',
                    color: isSelected ? 'var(--primary)' : 'var(--muted)',
                    fontWeight: isSelected ? 700 : 500, fontSize: '0.8rem', cursor: 'pointer'
                  }}
                >
                  <Icon size={18} />
                  <span>{r.label}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Quick Demo Fill Bar */}
        {!isRegistering && (
          <div style={{ backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-sm)', padding: '0.85rem', marginBottom: '1.5rem', border: '1px solid var(--border)' }}>
            <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              {t('demo_credentials_title')}
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              <button
                type="button"
                onClick={() => handleQuickFill('farmer')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600 }}
              >
                🌾 Demo Farmer
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('agent')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600 }}
              >
                🤝 Demo Agent
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('centre')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600 }}
              >
                🏢 Demo Centre
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('government')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600 }}
              >
                🏛️ Demo Govt Admin
              </button>
            </div>
          </div>
        )}

        {error && (
          <div style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem', backgroundColor: 'var(--danger-bg)', color: 'var(--danger-text)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* LOGIN FORM */}
        {!isRegistering ? (
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                {t('user_id_label')}
              </label>
              <input
                type="text"
                required
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder={role === 'government' ? 'admin@bharatagri.demo' : `${role}@bharatagri.demo`}
                style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                {t('password_label')}
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '0.5rem', padding: '0.8rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary)', color: '#ffffff', border: 'none',
                fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer', display: 'flex',
                alignItems: 'center', justifyContent: 'center', gap: '0.5rem'
              }}
            >
              <LogIn size={18} />
              {loading ? 'Authenticating...' : t('sign_in_btn')}
            </button>

            {(role === 'farmer' || role === 'centre') && (
              <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.85rem' }}>
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => setIsRegistering(true)}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
                >
                  Register here
                </button>
              </div>
            )}
          </form>
        ) : (
          /* REGISTRATION FORM */
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                {role === 'farmer' ? 'Full Name *' : 'Procurement Centre Name *'}
              </label>
              <input
                type="text"
                required
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                placeholder={role === 'farmer' ? 'e.g. Ramesh Naik' : 'e.g. Ponda Agricultural Mandi'}
                style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  User ID / Code *
                </label>
                <input
                  type="text"
                  required
                  value={regId}
                  onChange={(e) => setRegId(e.target.value)}
                  placeholder="Choose unique ID"
                  style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Password *
                </label>
                <input
                  type="password"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>
            </div>

            {role === 'farmer' ? (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                    Mobile Number *
                  </label>
                  <input
                    type="tel"
                    required
                    value={regMobile}
                    onChange={(e) => setRegMobile(e.target.value)}
                    placeholder="10-digit mobile"
                    style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                    Village / Locality *
                  </label>
                  <input
                    type="text"
                    required
                    value={regVillage}
                    onChange={(e) => setRegVillage(e.target.value)}
                    style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                  />
                </div>
              </div>
            ) : (
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                  Location / Yard Address *
                </label>
                <input
                  type="text"
                  required
                  value={regLocation}
                  onChange={(e) => setRegLocation(e.target.value)}
                  style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: '0.5rem', padding: '0.8rem', borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--primary)', color: '#ffffff', border: 'none',
                fontWeight: 700, fontSize: '0.95rem', cursor: 'pointer'
              }}
            >
              {loading ? 'Creating Account...' : 'Complete Registration'}
            </button>

            <div style={{ textAlign: 'center', marginTop: '0.5rem', fontSize: '0.85rem' }}>
              Already registered?{' '}
              <button
                type="button"
                onClick={() => setIsRegistering(false)}
                style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
              >
                Back to Sign in
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
