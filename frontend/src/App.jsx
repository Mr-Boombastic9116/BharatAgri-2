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
import { ThemeProvider } from './context/ThemeContext';
import { LanguageProvider } from './context/LanguageContext';

function AppContent() {
  // User state persisted in localStorage
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('bharatagri_user');
    return saved ? JSON.parse(saved) : null;
  });

  const [activePage, setActivePage] = useState(() => {
    const savedPage = localStorage.getItem('bharatagri_active_page');
    const savedUser = localStorage.getItem('bharatagri_user');
    if (savedPage) return savedPage;
    if (savedUser) {
      try {
        const u = JSON.parse(savedUser);
        const r = (u.role || '').toLowerCase();
        if (r === 'farmer') return 'farmer-dashboard';
        if (r === 'agent') return 'agent-dashboard';
        if (r === 'government' || r === 'admin') return 'government-dashboard';
        return 'centre-dashboard';
      } catch (e) {
        return 'home';
      }
    }
    return 'home';
  });
  const [initialLoginRole, setInitialLoginRole] = useState('farmer');

  // Active booking for confirmation view
  const [confirmedBooking, setConfirmedBooking] = useState(null);

  const navigate = (page, options = {}) => {
    if (options.role) {
      setInitialLoginRole(options.role);
    }
    setActivePage(page);
    localStorage.setItem('bharatagri_active_page', page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem('bharatagri_user', JSON.stringify(userData));
    const r = (userData.role || '').toLowerCase();
    if (r === 'farmer') {
      navigate('farmer-dashboard');
    } else if (r === 'agent') {
      navigate('agent-dashboard');
    } else if (r === 'government' || r === 'admin') {
      navigate('government-dashboard');
    } else {
      navigate('centre-dashboard');
    }
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('bharatagri_user');
    navigate('home');
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

          {activePage === 'centre-dashboard' && user && (user.role?.toLowerCase() === 'centre' || user.role?.toLowerCase() === 'procurement_centre') && (
            <CentreDashboard
              user={user}
            />
          )}

          {activePage === 'government-dashboard' && user && (user.role?.toLowerCase() === 'government' || user.role?.toLowerCase() === 'admin') && (
            <GovernmentDashboard
              user={user}
            />
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
