import React from 'react';
import {
  Sprout, LogOut, LogIn, Home, Info, User, Building2, Calendar,
  LayoutDashboard, Moon, Sun, Globe, Users, Briefcase
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useTranslation } from '../context/LanguageContext';

export default function Navbar({ user, activePage, navigate, onLogout }) {
  const { isDark, toggleTheme } = useTheme();
  const { lang, setLang, t } = useTranslation();

  const getDashboardPage = (role) => {
    const r = role?.toLowerCase();
    if (r === 'farmer') return 'farmer-dashboard';
    if (r === 'agent') return 'agent-dashboard';
    if (r === 'government' || r === 'admin') return 'government-dashboard';
    return 'centre-dashboard';
  };

  const getRoleIcon = (role) => {
    const r = role?.toLowerCase();
    if (r === 'farmer') return <User size={16} />;
    if (r === 'agent') return <Users size={16} />;
    if (r === 'government' || r === 'admin') return <Briefcase size={16} />;
    return <Building2 size={16} />;
  };

  return (
    <header className="navbar" style={{ borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-card)' }}>
      <div className="container navbar-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '64px' }}>
        <div className="brand-logo" onClick={() => navigate('home')} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div className="brand-logo-icon" style={{ backgroundColor: 'var(--primary)', color: '#ffffff', width: '36px', height: '36px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sprout size={22} />
          </div>
          <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.5px', color: 'var(--secondary)' }}>
            BHARAT<span style={{ color: 'var(--primary)' }}>AGRI</span>
          </span>
        </div>

        <nav>
          <ul className="nav-links" style={{ display: 'flex', alignItems: 'center', gap: '14px', margin: 0, listStyle: 'none' }}>
            <li
              className={`nav-link ${activePage === 'home' ? 'active' : ''}`}
              onClick={() => navigate('home')}
              style={{ cursor: 'pointer' }}
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem', fontWeight: 500 }}>
                <Home size={15} /> {t('home')}
              </span>
            </li>

            <li
              className={`nav-link ${activePage === 'about' ? 'active' : ''}`}
              onClick={() => navigate('about')}
              style={{ cursor: 'pointer' }}
            >
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem', fontWeight: 500 }}>
                <Info size={15} /> {t('about')}
              </span>
            </li>

            {user ? (
              <>
                <li
                  className={`nav-link ${activePage.includes('dashboard') ? 'active' : ''}`}
                  onClick={() => navigate(getDashboardPage(user.role))}
                  style={{ cursor: 'pointer' }}
                >
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem', fontWeight: 600, color: 'var(--primary)' }}>
                    {getRoleIcon(user.role)} {t('dashboard')}
                  </span>
                </li>

                {user.role?.toLowerCase() === 'farmer' && (
                  <li
                    className={`nav-link ${activePage === 'book-slot' ? 'active' : ''}`}
                    onClick={() => navigate('book-slot')}
                    style={{ cursor: 'pointer' }}
                  >
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem', fontWeight: 500 }}>
                      <Calendar size={15} /> {t('book_slot')}
                    </span>
                  </li>
                )}

                <li>
                  <div className="user-badge" style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 10px', backgroundColor: 'var(--bg-page)', borderRadius: '20px', border: '1px solid var(--border)' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--secondary)' }}>
                      {user.name} ({user.role?.toUpperCase()})
                    </span>
                    <button
                      onClick={onLogout}
                      className="btn btn-outline btn-sm"
                      title={t('logout')}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 8px', borderRadius: '12px', fontSize: '0.75rem' }}
                    >
                      <LogOut size={12} /> {t('logout')}
                    </button>
                  </div>
                </li>
              </>
            ) : (
              <li
                className={`nav-link ${activePage === 'login' ? 'active' : ''}`}
                onClick={() => navigate('login')}
                style={{ cursor: 'pointer' }}
              >
                <button className="btn btn-primary btn-sm" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '0.4rem 0.9rem', borderRadius: 'var(--radius-sm)' }}>
                  <LogIn size={14} /> {t('login')}
                </button>
              </li>
            )}

            {/* Language Switcher */}
            <li>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', border: '1px solid var(--border)', borderRadius: '16px', padding: '2px 6px', backgroundColor: 'var(--bg-page)' }}>
                <Globe size={13} color="var(--muted)" />
                <select
                  value={lang}
                  onChange={(e) => setLang(e.target.value)}
                  style={{
                    border: 'none', background: 'transparent', fontSize: '0.78rem',
                    fontWeight: 600, color: 'var(--secondary)', outline: 'none', cursor: 'pointer'
                  }}
                  aria-label="Language selector"
                >
                  <option value="en">EN</option>
                  <option value="hi">हिंदी</option>
                  <option value="mr">मराठी</option>
                </select>
              </div>
            </li>

            {/* Dark Mode Toggle */}
            <li>
              <button
                onClick={toggleTheme}
                title={isDark ? t('light_mode') : t('dark_mode')}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  width: '32px', height: '32px', borderRadius: '50%',
                  border: '1px solid var(--border)', backgroundColor: 'var(--bg-page)',
                  color: 'var(--secondary)', cursor: 'pointer'
                }}
                aria-label="Toggle dark mode"
              >
                {isDark ? <Sun size={15} color="#facc15" /> : <Moon size={15} color="var(--muted)" />}
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}
