import React, { useState } from 'react';
import { loginUser, registerFarmer, registerCentre, registerAgent, registerGovernment } from '../services/api';
import { LogIn, UserCheck, Building2, User, AlertCircle, ShieldCheck, Users, Briefcase, Sprout, Landmark } from 'lucide-react';
import { useTranslation } from '../context/LanguageContext';

const DEMO_ACCOUNTS = {
  farmer: { email: 'farmer@bharatagri.demo', password: 'BharatAgri@2026', role: 'FARMER' },
  agent: { email: 'agent@bharatagri.demo', password: 'BharatAgri@2026', role: 'AGENT' },
  centre: { email: 'centre@bharatagri.demo', password: 'BharatAgri@2026', role: 'PROCUREMENT_CENTRE' },
  government: { email: 'admin@bharatagri.demo', password: 'BharatAgri@2026', role: 'GOVERNMENT' }
};

const REGIONAL_STATE_CROPS = {
  Goa: ['Mango', 'Banana', 'Tomato'],
  Maharashtra: ['Sugarcane', 'Wheat', 'Cotton'],
  Karnataka: ['Paddy', 'Maize', 'Bajra']
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
  const [regEmail, setRegEmail] = useState('');
  const [regDob, setRegDob] = useState('1985-05-15');
  const [regVillage, setRegVillage] = useState('Ponda');
  const [regTaluka, setRegTaluka] = useState('Ponda');
  const [regDistrict, setRegDistrict] = useState('North Goa');
  const [regState, setRegState] = useState('Goa');
  const [regCrop, setRegCrop] = useState('Mango');
  const [regLandArea, setRegLandArea] = useState('2.5');
  const [regBankName, setRegBankName] = useState('State Bank of India');
  const [regBankAccount, setRegBankAccount] = useState('10293847561');
  const [regBankIfsc, setRegBankIfsc] = useState('SBIN0001234');
  const [regId, setRegId] = useState('');
  const [regFarmerCode, setRegFarmerCode] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regLanguage, setRegLanguage] = useState('English');

  // Agent Register State
  const [regAgencyName, setRegAgencyName] = useState('Goa Farmers Federation');
  const [regLicenseNo, setRegLicenseNo] = useState('APMC-LIC-2026-089');

  // Govt Register State
  const [regDepartment, setRegDepartment] = useState('Department of Food & Public Distribution');
  const [regDesignation, setRegDesignation] = useState('District Procurement Officer');
  const [regEmployeeId, setRegEmployeeId] = useState('GOV-OFF-5501');

  // Centre Register State
  const [regLocation, setRegLocation] = useState('Ponda, Goa');
  const [regContact, setRegContact] = useState('9876543210');
  const [regOperatingDays, setRegOperatingDays] = useState('Monday,Tuesday,Wednesday,Thursday,Friday,Saturday');
  const [regOpeningTime, setRegOpeningTime] = useState('09:00 AM');
  const [regClosingTime, setRegClosingTime] = useState('05:00 PM');
  const [regCrops, setRegCrops] = useState('Mango,Banana,Tomato');

  // Error & Loading States
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleStateChange = (newState) => {
    setRegState(newState);
    const stateCrops = REGIONAL_STATE_CROPS[newState] || ['Paddy', 'Wheat'];
    setRegCrop(stateCrops[0]);
    setRegCrops(stateCrops.join(','));
    if (newState === 'Goa') setRegDistrict('North Goa');
    else if (newState === 'Maharashtra') setRegDistrict('Pune');
    else if (newState === 'Karnataka') setRegDistrict('Bengaluru Rural');
  };

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
      setError('Please fill in all mandatory account fields (Name, Login ID, Password).');
      return;
    }

    setLoading(true);
    try {
      let registeredUser;
      if (role === 'farmer') {
        if (!regMobile.trim() || !regVillage.trim() || !regTaluka.trim() || !regDistrict.trim()) {
          setError('Mobile number, Village, Taluka, and District are required for Farmer registration.');
          setLoading(false);
          return;
        }
        if (!regBankAccount.trim() || !regBankIfsc.trim() || !regBankName.trim()) {
          setError('Bank details (Account No, IFSC, Bank Name) are required for DBT settlements.');
          setLoading(false);
          return;
        }
        const cleanFarmerCode = regFarmerCode.trim() || `FRM-2026-${Math.floor(10000 + Math.random() * 90000)}`;
        registeredUser = await registerFarmer({
          name: regName.trim(),
          mobile: regMobile.trim(),
          email: regEmail.trim() || undefined,
          dob: regDob || undefined,
          village: regVillage.trim(),
          taluka: regTaluka.trim(),
          district: regDistrict.trim(),
          state: regState.trim(),
          land_area: parseFloat(regLandArea) || 2.5,
          crop_name: regCrop,
          user_id: regId.trim(),
          user_code: regId.trim(),
          farmer_id: cleanFarmerCode,
          bank_name: regBankName.trim(),
          bank_account_no: regBankAccount.trim(),
          bank_ifsc: regBankIfsc.trim(),
          password: regPassword,
          preferred_language: regLanguage
        });
      } else if (role === 'agent') {
        if (!regAgencyName.trim() || !regLicenseNo.trim() || !regMobile.trim()) {
          setError('Agency Name, License Number, and Mobile Contact are required for Agent registration.');
          setLoading(false);
          return;
        }
        registeredUser = await registerAgent({
          name: regName.trim(),
          user_id: regId.trim(),
          password: regPassword,
          mobile: regMobile.trim(),
          email: regEmail.trim() || `${regId.trim()}@bharatagri.demo`,
          district: regDistrict.trim() || 'North Goa',
          state: regState.trim() || 'Goa',
          agency_name: regAgencyName.trim(),
          license_number: regLicenseNo.trim()
        });
      } else if (role === 'centre') {
        if (!regLocation.trim() || !regContact.trim() || !regCrops.trim()) {
          setError('Yard Address, Contact Phone, and Supported Commodities are required for Centre registration.');
          setLoading(false);
          return;
        }
        registeredUser = await registerCentre(
          regName.trim(),
          regId.trim(),
          regPassword,
          regLocation.trim(),
          regContact.trim(),
          regOperatingDays,
          regOpeningTime,
          regClosingTime,
          regCrops.trim(),
          regState.trim() || 'Goa',
          regDistrict.trim() || 'North Goa'
        );
      } else if (role === 'government') {
        if (!regDepartment.trim() || !regDesignation.trim() || !regEmployeeId.trim()) {
          setError('Department, Designation, and Employee ID are required for Government Official registration.');
          setLoading(false);
          return;
        }
        registeredUser = await registerGovernment({
          name: regName.trim(),
          user_id: regId.trim(),
          password: regPassword,
          email: regEmail.trim() || `${regId.trim()}@nic.in`,
          mobile: regMobile.trim() || '9876543210',
          department: regDepartment.trim(),
          designation: regDesignation.trim(),
          employee_id: regEmployeeId.trim(),
          state: regState.trim() || 'Goa',
          district: regDistrict.trim() || 'All'
        });
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
            {isRegistering 
              ? (role === 'farmer' ? 'Register as Farmer' : (role === 'agent' ? 'Register as APMC Agent' : (role === 'centre' ? 'Register Procurement Centre' : 'Register Government Official')))
              : t('login_title')}
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
            {isRegistering ? 'Direct Portal Registration for BharatAgri v2 Procurement Network' : t('app_tagline')}
          </p>
        </div>

        {/* 4 Roles Selector - Always visible */}
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
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              >
                <Sprout size={13} style={{ color: 'var(--primary)' }} /> Demo Farmer
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('agent')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              >
                <Users size={13} style={{ color: 'var(--info)' }} /> Demo Agent
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('centre')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              >
                <Building2 size={13} style={{ color: 'var(--secondary)' }} /> Demo Centre
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill('government')}
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem', borderRadius: '4px', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)', cursor: 'pointer', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
              >
                <Landmark size={13} style={{ color: 'var(--primary)' }} /> Demo Govt Admin
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

            <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.85rem' }}>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => setIsRegistering(true)}
                style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
              >
                Register as {role.toUpperCase()}
              </button>
            </div>
          </form>
        ) : (
          /* REGISTRATION FORM */
          <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                {role === 'farmer' ? 'Full Name *' : (role === 'agent' ? 'Agent / Entity Name *' : (role === 'centre' ? 'Procurement Centre Name *' : 'Official Full Name *'))}
              </label>
              <input
                type="text"
                required
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                placeholder={role === 'farmer' ? 'e.g. Ramesh Naik' : (role === 'agent' ? 'e.g. Suresh Agrawal' : (role === 'centre' ? 'e.g. Ponda Agricultural Mandi' : 'e.g. Dr. Rajesh Sharma'))}
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
                  placeholder="Choose unique user ID"
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

            {/* FARMER SPECIFIC */}
            {role === 'farmer' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Farmer ID (Optional / Auto)
                    </label>
                    <input
                      type="text"
                      value={regFarmerCode}
                      onChange={(e) => setRegFarmerCode(e.target.value)}
                      placeholder="e.g. FRM-2026-00042"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>

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
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      State *
                    </label>
                    <select
                      value={regState}
                      onChange={(e) => handleStateChange(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    >
                      <option value="Goa">Goa</option>
                      <option value="Maharashtra">Maharashtra</option>
                      <option value="Karnataka">Karnataka</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Primary Crop for MSP Registration *
                    </label>
                    <select
                      value={regCrop}
                      onChange={(e) => setRegCrop(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    >
                      {(REGIONAL_STATE_CROPS[regState] || ['Paddy']).map(crop => (
                        <option key={crop} value={crop}>{crop}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      District *
                    </label>
                    <input
                      type="text"
                      required
                      value={regDistrict}
                      onChange={(e) => setRegDistrict(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Taluka *
                    </label>
                    <input
                      type="text"
                      required
                      value={regTaluka}
                      onChange={(e) => setRegTaluka(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1rem' }}>
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
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Land Area (Ha) *
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      required
                      value={regLandArea}
                      onChange={(e) => setRegLandArea(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                {/* Bank Details */}
                <div style={{ border: '1px dashed var(--border)', borderRadius: 'var(--radius-sm)', padding: '0.85rem', backgroundColor: 'var(--primary-light)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-hover)', marginBottom: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>SECURE BANKING ACCOUNT (FOR DIRECT BENEFIT MSP TRANSFER)</span>
                    {regBankAccount.length > 4 && (
                      <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                        Preview: {'*'.repeat(Math.max(0, regBankAccount.length - 4)) + regBankAccount.slice(-4)}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr 1fr', gap: '0.75rem' }}>
                    <div>
                      <input
                        type="text"
                        required
                        value={regBankName}
                        onChange={(e) => setRegBankName(e.target.value)}
                        placeholder="Bank Name"
                        style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }}
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        required
                        value={regBankAccount}
                        onChange={(e) => setRegBankAccount(e.target.value)}
                        placeholder="Bank Account Number"
                        style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }}
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        required
                        value={regBankIfsc}
                        onChange={(e) => setRegBankIfsc(e.target.value.toUpperCase())}
                        placeholder="IFSC Code (e.g. SBIN0001234)"
                        style={{ width: '100%', padding: '0.6rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-card)', color: 'var(--secondary)' }}
                      />
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* AGENT SPECIFIC */}
            {role === 'agent' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Agency / Entity Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={regAgencyName}
                      onChange={(e) => setRegAgencyName(e.target.value)}
                      placeholder="e.g. Goa Farmers Federation"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      APMC / Trader License No *
                    </label>
                    <input
                      type="text"
                      required
                      value={regLicenseNo}
                      onChange={(e) => setRegLicenseNo(e.target.value)}
                      placeholder="e.g. APMC-LIC-2026-089"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Mobile Contact *
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
                      Official Email
                    </label>
                    <input
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="agent@example.com"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      State *
                    </label>
                    <input
                      type="text"
                      required
                      value={regState}
                      onChange={(e) => setRegState(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      District *
                    </label>
                    <input
                      type="text"
                      required
                      value={regDistrict}
                      onChange={(e) => setRegDistrict(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>
              </>
            )}

            {/* CENTRE SPECIFIC */}
            {role === 'centre' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Operating State *
                    </label>
                    <select
                      value={regState}
                      onChange={(e) => handleStateChange(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    >
                      <option value="Goa">Goa</option>
                      <option value="Maharashtra">Maharashtra</option>
                      <option value="Karnataka">Karnataka</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      District *
                    </label>
                    <input
                      type="text"
                      required
                      value={regDistrict}
                      onChange={(e) => setRegDistrict(e.target.value)}
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                    Yard / Godown Address *
                  </label>
                  <input
                    type="text"
                    required
                    value={regLocation}
                    onChange={(e) => setRegLocation(e.target.value)}
                    placeholder="e.g. APMC Market Yard, Ponda, Goa"
                    style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Contact Phone *
                    </label>
                    <input
                      type="tel"
                      required
                      value={regContact}
                      onChange={(e) => setRegContact(e.target.value)}
                      placeholder="10-digit number"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Supported Commodities *
                    </label>
                    <input
                      type="text"
                      required
                      value={regCrops}
                      onChange={(e) => setRegCrops(e.target.value)}
                      placeholder="e.g. Paddy,Wheat,Maize"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>
              </>
            )}

            {/* GOVERNMENT SPECIFIC */}
            {role === 'government' && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Ministry / Department *
                    </label>
                    <input
                      type="text"
                      required
                      value={regDepartment}
                      onChange={(e) => setRegDepartment(e.target.value)}
                      placeholder="e.g. Department of Food & Public Distribution"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Official Designation *
                    </label>
                    <input
                      type="text"
                      required
                      value={regDesignation}
                      onChange={(e) => setRegDesignation(e.target.value)}
                      placeholder="e.g. District Procurement Officer"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Government Employee ID *
                    </label>
                    <input
                      type="text"
                      required
                      value={regEmployeeId}
                      onChange={(e) => setRegEmployeeId(e.target.value)}
                      placeholder="e.g. GOV-OFF-5501"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Official Gov / NIC Email
                    </label>
                    <input
                      type="email"
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="officer@nic.in"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Jurisdiction State *
                    </label>
                    <input
                      type="text"
                      required
                      value={regState}
                      onChange={(e) => setRegState(e.target.value)}
                      placeholder="e.g. Goa"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.3rem', color: 'var(--secondary)' }}>
                      Jurisdiction District
                    </label>
                    <input
                      type="text"
                      value={regDistrict}
                      onChange={(e) => setRegDistrict(e.target.value)}
                      placeholder="e.g. North Goa or All"
                      style={{ width: '100%', padding: '0.7rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)', color: 'var(--secondary)' }}
                    />
                  </div>
                </div>
              </>
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
              {loading ? 'Creating Authorized Account...' : `Complete ${role.toUpperCase()} Registration`}
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
