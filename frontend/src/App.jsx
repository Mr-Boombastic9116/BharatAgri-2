import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import AboutUsPage from './pages/AboutUsPage';
import LoginPage from './pages/LoginPage';
import FarmerDashboard from './pages/FarmerDashboard';
import AgentDashboard from './pages/AgentDashboard';
import CentreDashboard from './pages/CentreDashboard';
import GovernmentDashboard from './pages/GovernmentDashboard';
import SlotBookingPage from './pages/SlotBookingPage';
import BookingConfirmationPage from './pages/BookingConfirmationPage';
import MyBookingPage from './pages/MyBookingPage';
import ProcessAppointmentPage from './pages/ProcessAppointmentPage';
import StoragePage from './pages/StoragePage';
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './context/LanguageContext';
import ErrorBoundary from './components/ErrorBoundary';

function AppContent() {
  // User state persisted in localStorage
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('bharatagri_user');
    return saved ? JSON.parse(saved) : null;
  });

  const normalizeRole = (role) => {
    return (role || '').toLowerCase().replace(/[-_ ]+/g, '_');
  };

  const isCentreRole = (role) => {
    const r = normalizeRole(role);
    return r === 'centre' || r === 'center' || r === 'procurement_centre' || r === 'procurement_center';
  };

  const getRoleDashboard = (role) => {
    const r = normalizeRole(role);
    if (r === 'farmer') return 'farmer-dashboard';
    if (r === 'agent') return 'agent-dashboard';
    if (r === 'government' || r === 'admin' || r === 'superadmin') return 'government-dashboard';
    if (isCentreRole(role)) return 'centre-dashboard';
    return 'home';
  };

  const isPageAuthorized = (page, currentUser) => {
    const r = normalizeRole(currentUser?.role);
    if (page === 'farmer-dashboard') return r === 'farmer';
    if (page === 'agent-dashboard') return r === 'agent';
    if (page === 'centre-dashboard' || page === 'centre-process' || page === 'centre-storage') {
      return isCentreRole(currentUser?.role);
    }
    if (page === 'government-dashboard') return r === 'government' || r === 'admin' || r === 'superadmin';
    if (page === 'book-slot' || page === 'my-booking') return r === 'farmer' || r === 'agent';
    if (page === 'copilot') {
      return ['government', 'admin', 'superadmin'].includes(r) || isCentreRole(currentUser?.role);
    }
    if (page === 'government-copilot') return ['government', 'admin', 'superadmin'].includes(r);
    if (page === 'centre-copilot') return isCentreRole(currentUser?.role);
    return true;
  };

  const getCurrentUser = () => {
    if (user) return user;
    try {
      const saved = localStorage.getItem('bharatagri_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  };

  const [activePage, setActivePage] = useState(() => {
    const hash = window.location.hash ? window.location.hash.replace(/^#\/?/, '').trim() : '';
    const savedUserStr = localStorage.getItem('bharatagri_user');
    let u = null;
    try {
      u = savedUserStr ? JSON.parse(savedUserStr) : null;
    } catch (e) {
      u = null;
    }

    const savedPage = hash || localStorage.getItem('bharatagri_active_page');
    const PROTECTED = [
      'farmer-dashboard', 'agent-dashboard', 'centre-dashboard', 'government-dashboard',
      'centre-process', 'centre-storage', 'book-slot', 'my-booking',
      'copilot', 'government-copilot', 'centre-copilot'
    ];

    if (savedPage && PROTECTED.includes(savedPage)) {
      if (!u) return 'login';
      if (!isPageAuthorized(savedPage, u)) return getRoleDashboard(u.role);
      return savedPage;
    }
    if (savedPage) return savedPage;
    if (u) return getRoleDashboard(u.role);
    return 'home';
  });

  const [initialLoginRole, setInitialLoginRole] = useState('farmer');

  // Active booking for confirmation view
  const [confirmedBooking, setConfirmedBooking] = useState(null);

  // Appointment ID for dedicated procurement processing workflow
  const [processAppointmentId, setProcessAppointmentId] = useState(() => {
    return localStorage.getItem('bharatagri_process_appointment_id') || null;
  });

  const navigate = (page, options = {}) => {
    if (options.role) {
      setInitialLoginRole(options.role);
    }
    if (options.appointmentId) {
      setProcessAppointmentId(options.appointmentId);
      localStorage.setItem('bharatagri_process_appointment_id', options.appointmentId);
    }

    const PROTECTED = [
      'farmer-dashboard', 'agent-dashboard', 'centre-dashboard', 'government-dashboard',
      'centre-process', 'centre-storage', 'book-slot', 'my-booking',
      'copilot', 'government-copilot', 'centre-copilot'
    ];
    let targetPage = page;
    const effectiveUser = getCurrentUser();
    if (PROTECTED.includes(page)) {
      if (!effectiveUser) {
        let roleHint = 'farmer';
        if (page.includes('centre')) roleHint = 'centre';
        else if (page.includes('agent')) roleHint = 'agent';
        else if (page.includes('gov')) roleHint = 'government';
        setInitialLoginRole(roleHint);
        targetPage = 'login';
      } else if (!isPageAuthorized(page, effectiveUser)) {
        targetPage = getRoleDashboard(effectiveUser.role);
      }
    }

    setActivePage(targetPage);
    localStorage.setItem('bharatagri_active_page', targetPage);
    window.location.hash = targetPage;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  useEffect(() => {
    const handleHashChange = () => {
      const hashPage = window.location.hash.replace(/^#\/?/, '').trim();
      if (!hashPage) return;

      const PROTECTED = [
        'farmer-dashboard', 'agent-dashboard', 'centre-dashboard', 'government-dashboard',
        'centre-process', 'centre-storage', 'book-slot', 'my-booking',
        'copilot', 'government-copilot', 'centre-copilot'
      ];
      if (PROTECTED.includes(hashPage)) {
        const effectiveUser = getCurrentUser();
        if (!effectiveUser) {
          let roleHint = 'farmer';
          if (hashPage.includes('centre')) roleHint = 'centre';
          else if (hashPage.includes('agent')) roleHint = 'agent';
          else if (hashPage.includes('gov')) roleHint = 'government';
          setInitialLoginRole(roleHint);
          setActivePage('login');
          window.location.hash = 'login';
          return;
        }
        if (!isPageAuthorized(hashPage, effectiveUser)) {
          const fallback = getRoleDashboard(effectiveUser.role);
          setActivePage(fallback);
          window.location.hash = fallback;
          return;
        }
      }
      setActivePage(hashPage);
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [user]);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem('bharatagri_user', JSON.stringify(userData));
    const targetDashboard = getRoleDashboard(userData.role);
    setActivePage(targetDashboard);
    localStorage.setItem('bharatagri_active_page', targetDashboard);
    window.location.hash = targetDashboard;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('bharatagri_user');
    localStorage.removeItem('bharatagri_active_page');
    window.location.hash = 'home';
    setActivePage('home');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBookingSuccess = (bookingData) => {
    setConfirmedBooking(bookingData);
    navigate('booking-confirmation');
  };

  return (
    <div className="app-container">
      <Navbar
        user={user}
        activePage={activePage}
        navigate={navigate}
        onLogout={handleLogout}
      />

      <main className="main-content">
        <div className="container">
          {activePage === 'home' && (
            <HomePage navigate={navigate} />
          )}

          {activePage === 'about' && (
            <AboutUsPage navigate={navigate} />
          )}

          {activePage === 'login' && (
            <LoginPage
              initialRole={initialLoginRole}
              onLoginSuccess={handleLoginSuccess}
              navigate={navigate}
            />
          )}

          {activePage === 'farmer-dashboard' && user && user.role?.toLowerCase() === 'farmer' && (
            <FarmerDashboard
              user={user}
              navigate={navigate}
            />
          )}

          {activePage === 'agent-dashboard' && user && user.role?.toLowerCase() === 'agent' && (
            <AgentDashboard
              user={user}
              navigate={navigate}
            />
          )}

          {(activePage === 'centre-dashboard' || (activePage === 'copilot' && isCentreRole(user?.role)) || activePage === 'centre-copilot') && user && isCentreRole(user.role) && (
            <ErrorBoundary title="Centre Operations Error" message="A rendering issue occurred in Centre Dashboard. Use reload or switch tabs to resume.">
              <CentreDashboard
                user={user}
                navigate={navigate}
                initialTab={(activePage === 'copilot' || activePage === 'centre-copilot') ? 'copilot' : 'overview'}
              />
            </ErrorBoundary>
          )}

          {activePage === 'centre-process' && user && (
            isCentreRole(user.role) || ['admin', 'government', 'superadmin'].includes(normalizeRole(user.role))
          ) && (
            <ProcessAppointmentPage
              user={user}
              appointmentId={processAppointmentId}
              navigate={navigate}
            />
          )}

          {activePage === 'centre-storage' && user && (
            isCentreRole(user.role) || ['admin', 'government', 'superadmin'].includes(normalizeRole(user.role))
          ) && (
            <StoragePage
              user={user}
              appointmentId={processAppointmentId}
              navigate={navigate}
            />
          )}

          {(activePage === 'government-dashboard' || (activePage === 'copilot' && ['government', 'admin', 'superadmin'].includes(normalizeRole(user?.role))) || activePage === 'government-copilot') && user && (['government', 'admin', 'superadmin'].includes(normalizeRole(user.role))) && (
            <ErrorBoundary title="Government Analytics Error" message="A rendering issue occurred in Government Dashboard. Use reload or switch tabs to resume.">
              <GovernmentDashboard
                user={user}
                navigate={navigate}
                initialTab={(activePage === 'copilot' || activePage === 'government-copilot') ? 'insights' : 'overview'}
              />
            </ErrorBoundary>
          )}

          {activePage === 'book-slot' && (
            <SlotBookingPage
              user={user}
              onBookingSuccess={handleBookingSuccess}
              navigate={navigate}
            />
          )}

          {activePage === 'booking-confirmation' && (
            <BookingConfirmationPage
              booking={confirmedBooking}
              navigate={navigate}
            />
          )}

          {activePage === 'my-booking' && user && (
            <MyBookingPage
              user={user}
              navigate={navigate}
            />
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <AppContent />
      </LanguageProvider>
    </ThemeProvider>
  );
}
