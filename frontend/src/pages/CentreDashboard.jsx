import React, { useEffect, useState, useRef } from 'react';
import { 
  getCentreBookings, 
  updateBookingStatus, 
  getSlots, 
  createSlot, 
  updateSlotCapacity, 
  deleteSlot, 
  verifyQrToken,
  getOperatingConfig,
  updateOperatingDays,
  addNonOperationalDate,
  removeNonOperationalDate,
  getDailyCapacity,
  updateDailyCapacity,
  applyScheduleRange
} from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { Html5Qrcode } from 'html5-qrcode';
import { 
  Building2, 
  Calendar, 
  Users, 
  Scale, 
  Clock, 
  Plus, 
  Check, 
  X, 
  UserCheck, 
  QrCode, 
  Camera, 
  AlertCircle, 
  Edit3, 
  Trash2, 
  Copy, 
  Layers, 
  Settings,
  CalendarOff,
  ChevronLeft,
  ChevronRight,
  ListFilter,
  Wheat
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';
import DateInput from '../components/DateInput';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function CentreDashboard({ user }) {
  // Navigation tab state: 'overview' | 'appointments' | 'slots' | 'config'
  const [activeTab, setActiveTab] = useState('overview');

  const todayStr = new Date().toISOString().split('T')[0];
  const [selectedDate, setSelectedDate] = useState(todayStr);

  const [bookings, setBookings] = useState([]);
  const [slots, setSlots] = useState([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Operating Config State
  const [operatingDays, setOperatingDays] = useState(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']);
  const [nonOperationalDates, setNonOperationalDates] = useState([]);
  const [savingOpDays, setSavingOpDays] = useState(false);

  // Add Non-Operational Date Form State
  const [newNonOpDate, setNewNonOpDate] = useState('');
  const [newNonOpReason, setNewNonOpReason] = useState('');
  const [addingNonOpDate, setAddingNonOpDate] = useState(false);

  // Daily Quintal Capacity State
  const [dailyCapacityInfo, setDailyCapacityInfo] = useState({ max_quintals_per_day: 500, booked_quintals: 0, available_quintals: 500 });
  const [editDailyQuintalVal, setEditDailyQuintalVal] = useState(500);
  const [savingDailyQuintal, setSavingDailyQuintal] = useState(false);
  const [showEditDailyQuintalModal, setShowEditDailyQuintalModal] = useState(false);

  // Slot Management State
  const [showAddSlotModal, setShowAddSlotModal] = useState(false);
  const [startTime, setStartTime] = useState('09:00 AM');
  const [endTime, setEndTime] = useState('11:00 AM');
  const [maxCap, setMaxCap] = useState(10);
  const [creatingSlot, setCreatingSlot] = useState(false);

  // Edit Slot Capacity Modal
  const [editingSlot, setEditingSlot] = useState(null);
  const [editCapValue, setEditCapValue] = useState(10);
  const [updatingCap, setUpdatingCap] = useState(false);

  // Date Range Generator Modal
  const [showRangeModal, setShowRangeModal] = useState(false);
  const [rangeStartDate, setRangeStartDate] = useState(todayStr);
  const [rangeEndDate, setRangeEndDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    return d.toISOString().split('T')[0];
  });
  const [rangeMaxQuintals, setRangeMaxQuintals] = useState(500);
  const [rangeTimeSlotsText, setRangeTimeSlotsText] = useState('09:00 AM - 11:00 AM, 11:00 AM - 01:00 PM, 02:00 PM - 04:00 PM');
  const [rangeSlotCap, setRangeSlotCap] = useState(10);
  const [generatingSchedule, setGeneratingSchedule] = useState(false);
  const [rangeSummary, setRangeSummary] = useState(null);

  // QR Verification Modal & Scanner state (Single transaction state machine)
  const [showQrModal, setShowQrModal] = useState(false);
  const [scannerState, setScannerState] = useState('inactive'); // 'inactive' | 'scanning' | 'processing' | 'result'
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [manualToken, setManualToken] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [verifying, setVerifying] = useState(false);

  const html5QrcodeRef = useRef(null);
  const isVerifyingRef = useRef(false);
  const hasScannedRef = useRef(false);
  const [updatingStatusId, setUpdatingStatusId] = useState(null);

  // Quick Date Navigation Handlers
  const handlePrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleToday = () => {
    setSelectedDate(todayStr);
  };

  const parseDaysArray = (daysVal) => {
    if (daysVal === '[object Object]') {
      return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    }
    let raw = [];
    if (Array.isArray(daysVal)) {
      raw = daysVal;
    } else if (typeof daysVal === 'string' && daysVal.trim()) {
      raw = daysVal.split(',').map(d => d.trim()).filter(Boolean);
    } else {
      return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    }

    const matched = [];
    for (const item of raw) {
      const found = WEEKDAYS.find(w => w.toLowerCase() === String(item).toLowerCase());
      if (found && !matched.includes(found)) {
        matched.push(found);
      }
    }
    return matched;
  };

  const loadCentreData = () => {
    if (user && user.user_id) {
      setLoading(true);
      Promise.all([
        getCentreBookings(user.user_id, selectedDate),
        getSlots(user.user_id, selectedDate),
        getOperatingConfig(user.user_id),
        getDailyCapacity(user.user_id, selectedDate)
      ])
        .then(([bookingsData, slotsData, configData, capData]) => {
          setBookings(bookingsData);
          setSlots(slotsData);
          setOperatingDays(parseDaysArray(configData.operating_days));
          setNonOperationalDates(configData.non_operational_dates || []);
          setDailyCapacityInfo(capData);
          setEditDailyQuintalVal(capData.max_quintals_per_day || 500);
        })
        .catch(err => setError('Failed to load centre data.'))
        .finally(() => setLoading(false));
    }
  };


  useEffect(() => {
    loadCentreData();
  }, [user, selectedDate]);

  const handleStatusChange = async (appointmentId, newStatus) => {
    if (updatingStatusId) return;
    setError('');
    setSuccessMsg('');
    setUpdatingStatusId(appointmentId);
    try {
      await updateBookingStatus(appointmentId, newStatus);
      setSuccessMsg(`Appointment ${appointmentId} status updated to ${newStatus}.`);
      
      // Immediately sync local frontend bookings array state
      setBookings(prevBookings =>
        prevBookings.map(b => {
          const match = (b.appointment_id === appointmentId) || (b.booking_id === appointmentId) || (b.id === appointmentId);
          return match ? { ...b, status: newStatus } : b;
        })
      );

      // Refresh overview summary & capacity stats in background
      loadCentreData();
    } catch (err) {
      setError(err.message || 'Failed to update status.');
    } finally {
      setUpdatingStatusId(null);
    }
  };

  // Toggle Weekly Operating Day Checkbox
  const handleToggleOperatingDay = (day) => {
    const currentDays = parseDaysArray(operatingDays);
    if (currentDays.includes(day)) {
      setOperatingDays(currentDays.filter(d => d !== day));
    } else {
      setOperatingDays([...currentDays, day]);
    }
  };


  // Save Weekly Operating Days
  const handleSaveOperatingDays = async () => {
    setError('');
    setSuccessMsg('');
    setSavingOpDays(true);
    try {
      const daysToSave = parseDaysArray(operatingDays);
      if (daysToSave.length === 0) {
        throw new Error('Please select at least one operational day.');
      }
      await updateOperatingDays(user.user_id, daysToSave);
      setSuccessMsg('Operating days updated successfully!');
      loadCentreData();
    } catch (err) {
      setError(err.message || 'Failed to update operating days.');
    } finally {
      setSavingOpDays(false);
    }
  };

  // Add Non-Operational Date
  const handleAddNonOpDate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    if (!newNonOpDate) {
      setError('Please select a date.');
      return;
    }
    setAddingNonOpDate(true);
    try {
      await addNonOperationalDate(user.user_id, newNonOpDate, newNonOpReason.trim() || 'Holiday / Centre Closed');
      setSuccessMsg(`Added ${newNonOpDate} to non-operational dates!`);
      setNewNonOpDate('');
      setNewNonOpReason('');
      loadCentreData();
    } catch (err) {
      setError(err.message || 'Failed to add non-operational date.');
    } finally {
      setAddingNonOpDate(false);
    }
  };

  // Remove Non-Operational Date
  const handleRemoveNonOpDate = async (date) => {
    setError('');
    setSuccessMsg('');
    try {
      await removeNonOperationalDate(user.user_id, date);
      setSuccessMsg(`Removed ${date} from non-operational dates.`);
      loadCentreData();
    } catch (err) {
      setError(err.message || 'Failed to remove non-operational date.');
    }
  };

  // Save Daily Quintal Capacity for Selected Date
  const handleSaveDailyCapacity = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    const newCap = parseFloat(editDailyQuintalVal);
    if (isNaN(newCap) || newCap <= 0) {
      setError('Daily capacity must be a positive number of Quintals.');
      return;
    }
    if (newCap < dailyCapacityInfo.booked_quintals) {
      setError(`Daily quintal capacity cannot be reduced below the existing booked quantity (${dailyCapacityInfo.booked_quintals} Quintals booked).`);
      return;
    }
    setSavingDailyQuintal(true);
    try {
      await updateDailyCapacity(user.user_id, selectedDate, newCap);
      setSuccessMsg(`Daily capacity for ${formatDateDisplay(selectedDate)} updated to ${newCap} Quintals!`);
      setShowEditDailyQuintalModal(false);
      loadCentreData();
    } catch (err) {
      setError(err.message || 'Failed to update daily capacity.');
    } finally {
      setSavingDailyQuintal(false);
    }
  };

  // Create Single Slot for Selected Date
  const handleCreateSlot = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!startTime.trim() || !endTime.trim()) {
      setError('Start time and End time are required.');
      return;
    }

    if (parseInt(maxCap, 10) <= 0) {
      setError('Maximum capacity must be greater than 0.');
      return;
    }

    setCreatingSlot(true);
    try {
      await createSlot(user.user_id, selectedDate, startTime.trim(), endTime.trim(), parseInt(maxCap, 10));
      setSuccessMsg(`New time slot (${startTime} - ${endTime}) added for ${formatDateDisplay(selectedDate)}!`);
      setShowAddSlotModal(false);
      const updatedSlots = await getSlots(user.user_id, selectedDate);
      setSlots(updatedSlots);
    } catch (err) {
      setError(err.message || 'Failed to create slot.');
    } finally {
      setCreatingSlot(false);
    }
  };

  // Save Slot Capacity
  const handleSaveCapacity = async (e) => {
    e.preventDefault();
    if (!editingSlot) return;

    setError('');
    setSuccessMsg('');
    const newCap = parseInt(editCapValue, 10);

    if (isNaN(newCap) || newCap <= 0) {
      setError('Capacity must be a positive number.');
      return;
    }

    if (newCap < editingSlot.booked_count) {
      setError(`Capacity cannot be lower than the number of existing bookings (${editingSlot.booked_count} booked).`);
      return;
    }

    setUpdatingCap(true);
    try {
      await updateSlotCapacity(editingSlot.id, newCap);
      setSuccessMsg(`Slot capacity updated to ${newCap} for ${editingSlot.start_time} - ${editingSlot.end_time}.`);
      setEditingSlot(null);
      const updatedSlots = await getSlots(user.user_id, selectedDate);
      setSlots(updatedSlots);
    } catch (err) {
      setError(err.message || 'Failed to update capacity.');
    } finally {
      setUpdatingCap(false);
    }
  };

  // Delete Slot
  const handleDeleteSlot = async (slotObj) => {
    setError('');
    setSuccessMsg('');

    if (slotObj.booked_count > 0) {
      setError(`Cannot delete slot with active bookings (${slotObj.booked_count} booked).`);
      return;
    }

    if (!window.confirm(`Are you sure you want to delete slot ${slotObj.start_time} - ${slotObj.end_time} for ${formatDateDisplay(selectedDate)}?`)) {
      return;
    }

    try {
      await deleteSlot(slotObj.id);
      setSuccessMsg(`Time slot deleted successfully.`);
      const updatedSlots = await getSlots(user.user_id, selectedDate);
      setSlots(updatedSlots);
    } catch (err) {
      setError(err.message || 'Failed to delete slot.');
    }
  };

  // Apply Date Range Generator
  const handleApplyScheduleRange = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setRangeSummary(null);

    if (!rangeStartDate || !rangeEndDate) {
      setError('Please select start and end dates.');
      return;
    }

    if (new Date(rangeEndDate) < new Date(rangeStartDate)) {
      setError('End date cannot be before start date.');
      return;
    }

    const rawSlots = rangeTimeSlotsText.split(',').map(s => s.trim()).filter(Boolean);
    const parsedSlots = rawSlots.map(s => {
      const parts = s.split('-').map(p => p.trim());
      return {
        start_time: parts[0] || '09:00 AM',
        end_time: parts[1] || '11:00 AM',
        max_capacity: parseInt(rangeSlotCap, 10) || 10
      };
    });

    setGeneratingSchedule(true);
    try {
      const result = await applyScheduleRange(
        user.user_id, 
        rangeStartDate, 
        rangeEndDate, 
        parsedSlots, 
        parseFloat(rangeMaxQuintals) || 500
      );
      setRangeSummary(result);
      setSuccessMsg(`Schedule range applied! ${result.created_dates_count} operating dates configured, ${result.skipped_dates_count} dates skipped due to closed days/holidays.`);
      loadCentreData();
    } catch (err) {
      setError(err.message || 'Failed to generate schedule range.');
    } finally {
      setGeneratingSchedule(false);
    }
  };

  // QR Verification Logic - Single Transaction State Flow
  const handleVerifyToken = async (tokenToVerify) => {
    if (!tokenToVerify || isVerifyingRef.current) return;
    isVerifyingRef.current = true;
    hasScannedRef.current = true;
    setScannerState('processing');
    setVerifying(true);
    setVerificationResult(null);

    // Stop scanner and camera hardware immediately upon detection
    await stopCameraScanner();

    try {
      const res = await verifyQrToken(tokenToVerify.trim(), user.user_id);
      setVerificationResult(res);
      setScannerState('result');
      if (res.success) {
        loadCentreData();
      }
    } catch (err) {
      setVerificationResult({
        success: false,
        code: 'ERROR',
        error: 'INVALID QR CODE ✕',
        message: err.message || 'Invalid or unverified QR code.'
      });
      setScannerState('result');
    } finally {
      setVerifying(false);
      isVerifyingRef.current = false;
    }
  };

  const startCameraScanner = async () => {
    await stopCameraScanner();
    setVerificationResult(null);
    setScannerState('scanning');
    setIsCameraActive(true);
    hasScannedRef.current = false;
    isVerifyingRef.current = false;

    setTimeout(async () => {
      try {
        const readerElement = document.getElementById("qr-reader");
        if (!readerElement) {
          setIsCameraActive(false);
          setScannerState('inactive');
          return;
        }

        const scanner = new Html5Qrcode("qr-reader");
        html5QrcodeRef.current = scanner;

        await scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: { width: 250, height: 250 } },
          (decodedText) => {
            // Strictly detect ONCE per attempt
            if (hasScannedRef.current) return;
            hasScannedRef.current = true;
            handleVerifyToken(decodedText);
          },
          () => {}
        );
      } catch (err) {
        console.warn("Camera start warning:", err);
        setError("Camera permission is required to scan the QR code.");
        setIsCameraActive(false);
        setScannerState('inactive');
      }
    }, 250);
  };

  const stopCameraScanner = async () => {
    // 1. Immediately terminate and release all video stream tracks
    try {
      const videoEl = document.querySelector('#qr-reader video');
      if (videoEl && videoEl.srcObject) {
        const stream = videoEl.srcObject;
        if (stream && stream.getTracks) {
          stream.getTracks().forEach(track => {
            try { track.stop(); } catch (e) {}
          });
        }
        videoEl.srcObject = null;
      }
    } catch (e) {
      console.warn("Error stopping video stream tracks:", e);
    }

    // 2. Stop and clear Html5Qrcode instance
    if (html5QrcodeRef.current) {
      try {
        if (html5QrcodeRef.current.isScanning) {
          await html5QrcodeRef.current.stop();
        }
        await html5QrcodeRef.current.clear();
      } catch (e) {
        console.warn("Error stopping html5Qrcode:", e);
      }
      html5QrcodeRef.current = null;
    }
    setIsCameraActive(false);
  };

  const openQrModal = () => {
    setError('');
    setVerificationResult(null);
    setManualToken('');
    hasScannedRef.current = false;
    isVerifyingRef.current = false;
    setShowQrModal(true);
    startCameraScanner();
  };

  const handleScanAnotherQr = () => {
    setVerificationResult(null);
    setManualToken('');
    setError('');
    hasScannedRef.current = false;
    isVerifyingRef.current = false;
    startCameraScanner();
  };

  const closeQrModal = async () => {
    hasScannedRef.current = true;
    isVerifyingRef.current = false;
    await stopCameraScanner();
    setShowQrModal(false);
    setScannerState('inactive');
    setVerificationResult(null);
    setManualToken('');
  };

  // ----------------------------------------------------
  // DATE-BASED COMPUTATIONS FOR SELECTED DATE
  // ----------------------------------------------------
  const holidayMatch = (nonOperationalDates || []).find(d => d.date === selectedDate);
  const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const selectedDayName = dayNames[new Date(selectedDate).getDay()];
  const opDaysArr = parseDaysArray(operatingDays);
  const isOperatingWeekday = opDaysArr.map(d => d.toLowerCase()).includes(selectedDayName.toLowerCase());

  const isClosedDate = Boolean(holidayMatch || !isOperatingWeekday);
  const closedReasonText = holidayMatch ? holidayMatch.reason : `${selectedDayName} is a non-operating weekday`;


  // Valid (non-rejected) bookings for selectedDate
  const validBookings = bookings.filter(b => b.status !== 'REJECTED');

  // Dynamic Crop-wise Aggregation
  const cropMap = {};
  validBookings.forEach(b => {
    const cropName = b.crop ? b.crop.trim() : 'Other';
    const qty = parseFloat(b.quantity || 0);
    if (!cropMap[cropName]) {
      cropMap[cropName] = { crop: cropName, total_bookings: 0, total_quintals: 0 };
    }
    cropMap[cropName].total_bookings += 1;
    cropMap[cropName].total_quintals += qty;
  });

  const cropSummaryList = Object.values(cropMap);
  const totalBookingsCount = validBookings.length;
  const totalQuintalsSum = validBookings.reduce((sum, b) => sum + parseFloat(b.quantity || 0), 0);

  // Total capacity calculations
  const totalCapacitySelectedDate = slots.reduce((sum, s) => sum + (s.max_capacity || 0), 0);
  const bookedCapacitySelectedDate = slots.reduce((sum, s) => sum + (s.booked_count || 0), 0);
  const remainingCapacitySelectedDate = Math.max(0, totalCapacitySelectedDate - bookedCapacitySelectedDate);

  return (
    <div className="centre-dashboard animate-fade-in">
      {/* Top Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: 'var(--secondary)' }}>
            Welcome, {user.name}
          </h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--muted)' }}>Procurement Centre Management & Date-based Portal</p>
        </div>

        <button 
          className="btn btn-primary btn-lg"
          onClick={openQrModal}
          style={{ boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <QrCode size={20} /> QR VERIFICATION
        </button>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.25rem' }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="alert alert-success" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1.25rem' }}>
          <Check size={18} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Centre Info Header Card */}
      <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', gap: '2rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Building2 size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>CENTRE NAME</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--secondary)' }}>{user.name}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Clock size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>CENTRE ID</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--secondary)' }}>{user.user_id}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: '#f0fdf4', color: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Scale size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>DAILY QUINTAL INTAKE CAP</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#15803d' }}>
              {dailyCapacityInfo.max_quintals_per_day} Quintals/Day
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tab Bar */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '1.75rem',
        borderBottom: '2px solid var(--border)',
        paddingBottom: '2px'
      }}>
        <button 
          className={`btn ${activeTab === 'overview' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('overview')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Calendar size={18} /> Overview & Summary
        </button>

        <button 
          className={`btn ${activeTab === 'appointments' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('appointments')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <ListFilter size={18} /> Appointments ({bookings.length})
        </button>

        <button 
          className={`btn ${activeTab === 'slots' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('slots')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Layers size={18} /> Date Schedule & Quintal Editor
        </button>

        <button 
          className={`btn ${activeTab === 'config' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('config')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Settings size={18} /> Operating Config & Holidays
        </button>
      </div>

      {/* UNIVERSAL TOP DATE SELECTION CONTROL (Applies across Overview, Appointments, and Schedule Editor) */}
      <div className="card shadow-sm mb-4" style={{ padding: '16px 24px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Calendar size={20} color="var(--primary)" />
            <label style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--secondary)', margin: 0 }}>
              Select Date:
            </label>
            <DateInput 
              id="centre-universal-selected-date"
              value={selectedDate}
              onChange={(newDate) => setSelectedDate(newDate)}
              style={{ width: '170px' }}
            />
          </div>

          {/* Quick Date Navigation Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button 
              className="btn btn-outline btn-sm"
              onClick={handlePrevDay}
              title="Previous Day"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              <ChevronLeft size={16} /> Previous Day
            </button>
            
            <button 
              className="btn btn-secondary btn-sm"
              onClick={handleToday}
              style={{ fontWeight: 700 }}
            >
              Today
            </button>

            <button 
              className="btn btn-outline btn-sm"
              onClick={handleNextDay}
              title="Next Day"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            >
              Next Day <ChevronRight size={16} />
            </button>
          </div>

          <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--primary-dark)', background: '#e0f2fe', padding: '6px 14px', borderRadius: '20px' }}>
            Selected Date: {formatDateDisplay(selectedDate)}
          </div>
        </div>
      </div>

      {/* TAB 1: DATE-BASED OVERVIEW & CROP SUMMARY */}
      {activeTab === 'overview' && (
        <>
          {/* HIERARCHY ITEM 1: CLOSED / NON-OPERATIONAL DATE NOTICE */}
          {isClosedDate ? (
            <div className="card shadow-sm mb-4" style={{ padding: '32px', textAlign: 'center', background: '#fef2f2', border: '1.5px solid #fca5a5', borderRadius: '14px' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: '#fee2e2', color: '#dc2626', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
                <CalendarOff size={32} />
              </div>
              <h2 style={{ fontSize: '1.6rem', color: '#991b1b', fontWeight: 800, marginBottom: '8px' }}>
                Centre Closed — {formatDateDisplay(selectedDate)}
              </h2>
              <p style={{ fontSize: '1rem', color: '#b91c1c', fontWeight: 600, margin: 0 }}>
                Reason: {closedReasonText}
              </p>
              <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginTop: '8px' }}>
                No crop procurement or appointment slots are scheduled for this date.
              </p>
            </div>
          ) : slots.length === 0 ? (
            /* HIERARCHY ITEM 1 ALT: NO SCHEDULE CONFIGURED FOR DATE */
            <div className="card shadow-sm mb-4" style={{ padding: '32px', textAlign: 'center', background: '#fafafa', border: '1px dashed var(--border)', borderRadius: '14px' }}>
              <Clock size={40} color="var(--muted)" style={{ marginBottom: '12px' }} />
              <h3 style={{ fontSize: '1.4rem', color: 'var(--secondary)', fontWeight: 700, marginBottom: '6px' }}>
                No Schedule Available for {formatDateDisplay(selectedDate)}
              </h3>
              <p style={{ fontSize: '0.95rem', color: 'var(--muted)', marginBottom: '16px' }}>
                No time slots have been configured for this date.
              </p>
              <button className="btn btn-primary" onClick={() => setActiveTab('slots')}>
                Go to Slot Management
              </button>
            </div>
          ) : (
            <>
              {/* HIERARCHY ITEM 2: DATE-SPECIFIC DAILY SUMMARY CARDS */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '16px',
                marginBottom: '1.5rem'
              }}>
                {/* Card 1: Daily Quintal Capacity */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      DAILY QUINTAL CAPACITY
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#e0f2fe', color: '#0284c7', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Scale size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--secondary)', lineHeight: 1.2 }}>
                      {dailyCapacityInfo.max_quintals_per_day || 0} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--muted)' }}>Quintals</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Max daily limit for {formatDateDisplay(selectedDate)}
                    </div>
                  </div>
                </div>

                {/* Card 2: Booked Quantity */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      BOOKED
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#f0fdf4', color: '#16a34a', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Wheat size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#15803d', lineHeight: 1.2 }}>
                      {dailyCapacityInfo.booked_quintals || 0} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#166534' }}>Quintals</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Booked total for {formatDateDisplay(selectedDate)}
                    </div>
                  </div>
                </div>

                {/* Card 3: Remaining Capacity */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      REMAINING
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#fff7ed', color: '#ea580c', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Clock size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#c2410c', lineHeight: 1.2 }}>
                      {Math.max(0, (dailyCapacityInfo.max_quintals_per_day || 0) - (dailyCapacityInfo.booked_quintals || 0))} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#9a3412' }}>Quintals</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      Remaining = Max ({dailyCapacityInfo.max_quintals_per_day || 0}) − Booked ({dailyCapacityInfo.booked_quintals || 0})
                    </div>
                  </div>
                </div>

                {/* Card 4: Total Appointments */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      Total Appointments
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: '#f3e8ff', color: '#7c3aed', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Users size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#6d28d9', lineHeight: 1.2 }}>
                      {totalBookingsCount} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--muted)' }}>Farmers</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                      {remainingCapacitySelectedDate} slot capacity available
                    </div>
                  </div>
                </div>
              </div>


              {/* HIERARCHY ITEM 3: CROP-WISE DAILY SUMMARY (IMPORTANT - Directly ABOVE Time Slots) */}
              <div className="card shadow-sm mb-4" style={{ padding: '24px', borderTop: '4px solid var(--primary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                    <Wheat size={22} color="var(--primary)" /> Crop Summary — {formatDateDisplay(selectedDate)}
                  </h3>
                  <span className="badge badge-confirmed" style={{ fontSize: '0.85rem' }}>
                    {cropSummaryList.length} Active Crops
                  </span>
                </div>

                {cropSummaryList.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '24px', background: '#fafafa', borderRadius: '8px', border: '1px dashed #e2e8f0' }}>
                    <Wheat size={32} color="var(--muted)" style={{ marginBottom: '8px' }} />
                    <h4 style={{ fontSize: '1.1rem', color: 'var(--secondary)', margin: '0 0 4px 0' }}>No crop bookings yet</h4>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0 }}>
                      There are no registered farmer bookings recorded for {formatDateDisplay(selectedDate)}.
                    </p>
                  </div>
                ) : (
                  <div className="table-container">
                    <table className="data-table" style={{ width: '100%' }}>
                      <thead>
                        <tr style={{ background: '#f8fafc' }}>
                          <th style={{ fontSize: '0.9rem', fontWeight: 700, padding: '12px 16px' }}>Crop</th>
                          <th style={{ fontSize: '0.9rem', fontWeight: 700, textAlign: 'right', padding: '12px 16px' }}>Total Bookings</th>
                          <th style={{ fontSize: '0.9rem', fontWeight: 700, textAlign: 'right', padding: '12px 16px' }}>Total Quintals</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cropSummaryList.map(item => (
                          <tr key={item.crop}>
                            <td style={{ fontWeight: 600, padding: '12px 16px' }}>
                              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--primary)' }}></span>
                                {item.crop}
                              </span>
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 700, padding: '12px 16px' }}>
                              {item.total_bookings} Farmers
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--primary-dark)', padding: '12px 16px' }}>
                              {item.total_quintals} Quintals
                            </td>
                          </tr>
                        ))}
                        {/* Dynamic Total Row */}
                        <tr style={{ background: '#f0fdf4', borderTop: '2px solid #bbf7d0' }}>
                          <td style={{ fontWeight: 800, fontSize: '1.05rem', color: '#14532d', padding: '14px 16px' }}>
                            Total
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 800, fontSize: '1.05rem', color: '#14532d', padding: '14px 16px' }}>
                            {totalBookingsCount} Bookings
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 800, fontSize: '1.1rem', color: '#16a34a', padding: '14px 16px' }}>
                            {totalQuintalsSum} Quintals
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* HIERARCHY ITEM 4: TIME SLOTS DISPLAY (Positioned Immediately BELOW Crop Summary) */}
              <div className="card shadow-sm mb-4" style={{ padding: '24px' }}>
                <div className="card-header" style={{ padding: 0, marginBottom: '16px' }}>
                  <h3 className="card-title" style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Time Slots — {formatDateDisplay(selectedDate)}
                  </h3>
                  <span style={{ fontSize: '0.85rem', color: 'var(--muted)', fontWeight: 600 }}>
                    {slots.length} Configured Slots
                  </span>
                </div>

                <div className="table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Time Slot</th>
                        <th style={{ textAlign: 'right' }}>Booked Farmers</th>
                        <th style={{ textAlign: 'right' }}>Capacity</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {slots.map(s => (
                        <tr key={s.id}>
                          <td><strong style={{ fontSize: '1rem', color: 'var(--secondary)' }}>{s.start_time} – {s.end_time}</strong></td>
                          <td style={{ textAlign: 'right' }}><strong>{s.booked_count}</strong></td>
                          <td style={{ textAlign: 'right' }}>{s.max_capacity}</td>
                          <td>
                            {s.is_full ? (
                              <span className="badge badge-rejected">Full</span>
                            ) : s.booked_count > 0 ? (
                              <span className="badge badge-pending">Partially Booked</span>
                            ) : (
                              <span className="badge badge-confirmed">Available</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* TAB 2: DATE-SPECIFIC APPOINTMENTS LIST */}
      {activeTab === 'appointments' && (
        <div className="card shadow-sm mb-4" style={{ padding: '24px' }}>
          <div className="card-header" style={{ padding: 0, marginBottom: '20px' }}>
            <div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--secondary)' }}>
                Appointments for {formatDateDisplay(selectedDate)}
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                Detailed farmer booking list for the selected date grouped by time slot.
              </p>
            </div>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary-dark)', background: '#e0f2fe', padding: '6px 12px', borderRadius: '8px' }}>
              Total: {bookings.length} Appointments
            </span>
          </div>

          {isClosedDate ? (
            <div style={{ textAlign: 'center', padding: '32px', background: '#fef2f2', borderRadius: '12px', border: '1px solid #fca5a5' }}>
              <h3 style={{ color: '#991b1b', fontWeight: 800 }}>Centre Closed on {formatDateDisplay(selectedDate)}</h3>
              <p style={{ color: '#b91c1c' }}>Reason: {closedReasonText}</p>
            </div>
          ) : loading ? (
            <p style={{ padding: '16px' }}>Loading appointments for {formatDateDisplay(selectedDate)}...</p>
          ) : bookings.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px', background: '#fafafa', borderRadius: '12px', border: '1px dashed #cbd5e1' }}>
              <Users size={40} color="var(--muted)" style={{ marginBottom: '12px' }} />
              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--secondary)', marginBottom: '6px' }}>No Appointments</h3>
              <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                There are no farmer appointments registered for {formatDateDisplay(selectedDate)}.
              </p>
            </div>
          ) : (
            /* Grouped Appointments by Time Slot */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {slots.map(slot => {
                const slotBookings = bookings.filter(b => b.slot_id === slot.id || (b.start_time === slot.start_time && b.end_time === slot.end_time));
                return (
                  <div key={slot.id} style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                    {/* Slot Group Header */}
                    <div style={{ background: '#f8fafc', padding: '14px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Clock size={18} color="var(--primary)" />
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                          {slot.start_time} – {slot.end_time}
                        </h3>
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.875rem', color: slot.is_full ? '#dc2626' : '#15803d' }}>
                        {slotBookings.length} / {slot.max_capacity} Farmers Booked
                      </span>
                    </div>

                    {/* Slot Appointment Table */}
                    {slotBookings.length === 0 ? (
                      <p style={{ padding: '16px 20px', color: 'var(--muted)', fontSize: '0.875rem', margin: 0 }}>
                        No farmers booked in this slot yet.
                      </p>
                    ) : (
                      <div className="table-container">
                        <table className="data-table" style={{ margin: 0 }}>
                          <thead>
                            <tr>
                              <th>Farmer Name</th>
                              <th>Mobile / ID</th>
                              <th>Appointment ID</th>
                              <th>Crop</th>
                              <th>Quantity</th>
                              <th>Status</th>
                              <th>Verification</th>
                              <th style={{ textAlign: 'center' }}>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {slotBookings.map(b => (
                              <tr key={b.id || b.appointment_id}>
                                <td><strong>{b.farmer_name}</strong></td>
                                <td>{b.farmer_mobile || b.farmer_id}</td>
                                <td><strong style={{ color: 'var(--primary)' }}>{b.appointment_id || b.booking_id}</strong></td>
                                <td>{b.crop}</td>
                                <td><strong>{b.quantity} Quintals</strong></td>
                                <td><StatusBadge status={b.status} /></td>
                                <td>
                                  {b.status === 'VERIFIED' ? (
                                    <span style={{ color: 'var(--success)', fontWeight: 800, fontSize: '0.85rem' }}>VERIFIED ✓</span>
                                  ) : (
                                    <span style={{ color: 'var(--muted)', fontWeight: 600, fontSize: '0.85rem' }}>NOT VERIFIED</span>
                                  )}
                                </td>
                                <td>
                                  <div style={{ display: 'flex', gap: '0.35rem', justifyContent: 'center' }}>
                                    {(b.status === 'BOOKED' || b.status === 'PENDING') && (
                                      <button 
                                        className="btn btn-success btn-sm"
                                        onClick={() => handleStatusChange(b.appointment_id || b.booking_id, 'CONFIRMED')}
                                        disabled={updatingStatusId === (b.appointment_id || b.booking_id)}
                                        title="Accept Appointment"
                                      >
                                        <Check size={14} /> Accept
                                      </button>
                                    )}

                                    {(b.status === 'BOOKED' || b.status === 'PENDING' || b.status === 'CONFIRMED') && (
                                      <button 
                                        className="btn btn-outline btn-sm"
                                        style={{ backgroundColor: '#e0f2fe', color: '#0369a1', borderColor: '#7dd3fc' }}
                                        onClick={() => handleStatusChange(b.appointment_id || b.booking_id, 'ARRIVED')}
                                        disabled={updatingStatusId === (b.appointment_id || b.booking_id)}
                                        title="Mark Farmer Arrived"
                                      >
                                        <UserCheck size={14} /> Arrived
                                      </button>
                                    )}

                                    {b.status !== 'REJECTED' && b.status !== 'VERIFIED' && (
                                      <button 
                                        className="btn btn-danger btn-sm"
                                        onClick={() => handleStatusChange(b.appointment_id || b.booking_id, 'REJECTED')}
                                        disabled={updatingStatusId === (b.appointment_id || b.booking_id)}
                                        title="Reject Appointment"
                                      >
                                        <X size={14} /> Reject
                                      </button>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: DATE SCHEDULE & DAILY QUINTAL CAPACITY EDITOR */}
      {activeTab === 'slots' && (
        <div className="card" style={{ marginBottom: '2.5rem' }}>
          {/* Header Controls */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '1.5rem',
            paddingBottom: '1rem',
            borderBottom: '1px solid var(--border)'
          }}>
            <div>
              <h2 style={{ fontSize: '1.4rem', color: 'var(--secondary)' }}>Date-by-Date Schedule & Quintal Capacity</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                Configure independent time slots and maximum daily intake limits (Quintals) for {formatDateDisplay(selectedDate)}.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <button 
                className="btn btn-primary btn-sm"
                onClick={() => setShowAddSlotModal(true)}
              >
                <Plus size={16} /> Add Slot
              </button>

              <button 
                className="btn btn-secondary btn-sm"
                onClick={() => setShowRangeModal(true)}
                title="Date Range Schedule Creator"
              >
                <Copy size={16} /> Date Range Creator
              </button>
            </div>
          </div>

          {/* Daily Quintal Capacity Banner */}
          <div style={{
            background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
            border: '1px solid #bbf7d0',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem'
          }}>
            <div>
              <div style={{ fontSize: '0.85rem', color: '#166534', fontWeight: 700, textTransform: 'uppercase' }}>
                Daily Quintal Capacity for {formatDateDisplay(selectedDate)}
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#14532d', marginTop: '4px' }}>
                {dailyCapacityInfo.booked_quintals} / {dailyCapacityInfo.max_quintals_per_day} Quintals Booked
              </div>
              <div style={{ fontSize: '0.875rem', color: '#15803d', marginTop: '2px' }}>
                Available: <strong>{dailyCapacityInfo.available_quintals} Quintals</strong> remaining for booking.
              </div>
            </div>

            <button 
              className="btn btn-primary btn-sm"
              onClick={() => {
                setEditDailyQuintalVal(dailyCapacityInfo.max_quintals_per_day);
                setShowEditDailyQuintalModal(true);
              }}
            >
              <Edit3 size={16} /> Edit Daily Limit
            </button>
          </div>

          {/* Schedule Row Table */}
          {loading ? (
            <p style={{ padding: '1rem' }}>Loading schedule for {formatDateDisplay(selectedDate)}...</p>
          ) : slots.length === 0 ? (
            <div style={{ padding: '2.5rem 1rem', textAlign: 'center', backgroundColor: 'var(--bg-page)', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border)' }}>
              <Clock size={36} color="var(--muted)" style={{ marginBottom: '0.5rem' }} />
              <h4 style={{ fontSize: '1.1rem', marginBottom: '0.35rem' }}>No Time Slots Configured for {formatDateDisplay(selectedDate)}</h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--muted)', marginBottom: '1.25rem' }}>
                Create time slots for this date or use the Date Range Creator to populate multiple operating days.
              </p>
              <button 
                className="btn btn-primary"
                onClick={() => setShowAddSlotModal(true)}
              >
                <Plus size={16} /> Add Time Slot
              </button>
            </div>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time Slot</th>
                    <th style={{ textAlign: 'right' }}>Max Farmers</th>
                    <th style={{ textAlign: 'right' }}>Booked Farmers</th>
                    <th style={{ textAlign: 'right' }}>Remaining Farmers</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'center' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {slots.map(s => (
                    <tr key={s.id}>
                      <td><strong style={{ fontSize: '1rem', color: 'var(--secondary)' }}>{s.start_time} – {s.end_time}</strong></td>
                      <td style={{ textAlign: 'right', fontWeight: 700 }}>{s.max_capacity}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: s.booked_count > 0 ? 'var(--primary)' : 'var(--muted)' }}>
                        {s.booked_count}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 700 }}>{s.remaining_capacity}</td>
                      <td>
                        {s.is_full ? (
                          <span className="badge badge-rejected">Full</span>
                        ) : s.booked_count > 0 ? (
                          <span className="badge badge-pending">Partially Booked</span>
                        ) : (
                          <span className="badge badge-confirmed">Available</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
                          <button 
                            className="btn btn-outline btn-sm"
                            onClick={() => {
                              setEditingSlot(s);
                              setEditCapValue(s.max_capacity);
                              setError('');
                            }}
                            title="Edit farmer capacity"
                          >
                            <Edit3 size={14} /> Edit
                          </button>

                          <button 
                            className="btn btn-danger btn-sm"
                            onClick={() => handleDeleteSlot(s)}
                            disabled={s.booked_count > 0}
                            title={s.booked_count > 0 ? "Cannot delete slot with active bookings" : "Delete slot"}
                          >
                            <Trash2 size={14} /> Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: OPERATING DAYS & HOLIDAYS CONFIGURATION */}
      {activeTab === 'config' && (
        <div className="grid grid-2" style={{ gap: '24px', marginBottom: '2.5rem' }}>
          {/* Section 1: Weekly Operating Days */}
          <div className="card shadow-sm" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={20} /> Weekly Operating Days
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Select which days of the week your procurement centre accepts crop deliveries.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              {WEEKDAYS.map(day => {
                const currentDays = parseDaysArray(operatingDays);
                const isChecked = currentDays.includes(day);
                return (
                  <label key={day} style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', padding: '8px 12px', borderRadius: '8px', background: isChecked ? '#f0fdf4' : '#f8fafc', border: `1px solid ${isChecked ? '#bbf7d0' : '#e2e8f0'}` }}>
                    <input 
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleOperatingDay(day)}
                      style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                    />
                    <span style={{ fontWeight: 600, color: isChecked ? '#166534' : 'var(--text-secondary)' }}>{day}</span>
                    {isChecked ? (
                      <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 700, color: '#16a34a', textTransform: 'uppercase' }}>Open</span>
                    ) : (
                      <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 700, color: '#dc2626', textTransform: 'uppercase' }}>Closed</span>
                    )}
                  </label>
                );
              })}
            </div>


            <button 
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={handleSaveOperatingDays}
              disabled={savingOpDays}
            >
              {savingOpDays ? 'Saving Operating Days...' : 'Save Weekly Operating Days'}
            </button>
          </div>

          {/* Section 2: Non-Operational Date Exceptions (Holidays) */}
          <div className="card shadow-sm" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: '#dc2626' }}>
              <CalendarOff size={20} /> Non-Operational Date Exceptions
            </h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Specify national holidays, maintenance days, or special closure dates.
            </p>

            {/* Add Holiday Form */}
            <form onSubmit={handleAddNonOpDate} style={{ marginBottom: '20px', background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Date</label>
                  <DateInput 
                    id="new-non-op-date"
                    value={newNonOpDate}
                    onChange={(newVal) => setNewNonOpDate(newVal)}
                    required
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Reason</label>
                  <input 
                    type="text"
                    className="form-control"
                    placeholder="e.g. Gandhi Jayanti"
                    value={newNonOpReason}
                    onChange={(e) => setNewNonOpReason(e.target.value)}
                  />
                </div>
              </div>

              <button 
                type="submit" 
                className="btn btn-danger btn-sm"
                style={{ width: '100%' }}
                disabled={addingNonOpDate}
              >
                + Add Non-Operational Date
              </button>
            </form>

            {/* List of Non-Operational Dates */}
            {nonOperationalDates.length === 0 ? (
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textAlign: 'center', padding: '16px', background: '#fafafa', borderRadius: '8px' }}>
                No holiday exceptions configured.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '320px', overflowY: 'auto' }}>
                {nonOperationalDates.map(item => (
                  <div key={item.date} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fef2f2', borderRadius: '8px', border: '1px solid #fecaca' }}>
                    <div>
                      <div style={{ fontWeight: 700, color: '#991b1b', fontSize: '0.9rem' }}>{formatDateDisplay(item.date)}</div>
                      <div style={{ fontSize: '0.8rem', color: '#b91c1c' }}>{item.reason}</div>
                    </div>
                    <button 
                      className="btn btn-danger btn-sm"
                      style={{ padding: '2px 8px', fontSize: '0.75rem' }}
                      onClick={() => handleRemoveNonOpDate(item.date)}
                      title="Remove Holiday Exception"
                    >
                      <Trash2 size={12} /> Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL 1: EDIT DAILY QUINTAL CAPACITY */}
      {showEditDailyQuintalModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }}>
            <div className="card-header">
              <h3 className="card-title">Edit Daily Quintal Capacity</h3>
            </div>

            <p style={{ fontSize: '0.9rem', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
              Set maximum total crop intake allowed for <strong>{formatDateDisplay(selectedDate)}</strong> across all slots.
            </p>

            <form onSubmit={handleSaveDailyCapacity}>
              <div className="form-group">
                <label className="form-label">Maximum Quintals Per Day</label>
                <input 
                  type="number"
                  step="0.1"
                  min={dailyCapacityInfo.booked_quintals || 1}
                  className="form-control"
                  value={editDailyQuintalVal}
                  onChange={(e) => setEditDailyQuintalVal(e.target.value)}
                  required
                />
                <small style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
                  Current Booked: {dailyCapacityInfo.booked_quintals} Quintals. Cannot be lower than booked total.
                </small>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  style={{ flex: 1 }}
                  onClick={() => setShowEditDailyQuintalModal(false)}
                >
                  Cancel
                </button>

                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  style={{ flex: 1 }}
                  disabled={savingDailyQuintal}
                >
                  {savingDailyQuintal ? 'Saving Limit...' : 'Save Limit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: ADD SINGLE TIME SLOT MODAL */}
      {showAddSlotModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '460px', width: '100%', padding: '2rem' }}>
            <div className="card-header">
              <h3 className="card-title">+ Add Time Slot for {formatDateDisplay(selectedDate)}</h3>
            </div>

            <form onSubmit={handleCreateSlot}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Start Time</label>
                  <input 
                    type="text"
                    className="form-control"
                    placeholder="e.g. 09:00 AM"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">End Time</label>
                  <input 
                    type="text"
                    className="form-control"
                    placeholder="e.g. 11:00 AM"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Maximum Farmers (Capacity)</label>
                <input 
                  type="number"
                  min="1"
                  className="form-control"
                  value={maxCap}
                  onChange={(e) => setMaxCap(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  style={{ flex: 1 }}
                  onClick={() => setShowAddSlotModal(false)}
                >
                  Cancel
                </button>

                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  style={{ flex: 1 }}
                  disabled={creatingSlot}
                >
                  {creatingSlot ? 'Adding Slot...' : 'Add Slot'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: EDIT SLOT FARMER CAPACITY MODAL */}
      {editingSlot && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2rem' }}>
            <div className="card-header">
              <h3 className="card-title">Edit Slot Farmer Capacity</h3>
            </div>

            <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
              Slot: <strong>{editingSlot.start_time} – {editingSlot.end_time}</strong> ({formatDateDisplay(selectedDate)})
            </p>

            <form onSubmit={handleSaveCapacity}>
              <div className="form-group">
                <label className="form-label">Maximum Farmers (Capacity)</label>
                <input 
                  type="number"
                  min={editingSlot.booked_count || 1}
                  className="form-control"
                  value={editCapValue}
                  onChange={(e) => setEditCapValue(e.target.value)}
                  required
                />
                <small style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>
                  Current Booked: {editingSlot.booked_count} farmers. Capacity cannot be lower than existing bookings.
                </small>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  style={{ flex: 1 }}
                  onClick={() => setEditingSlot(null)}
                >
                  Cancel
                </button>

                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  style={{ flex: 1 }}
                  disabled={updatingCap}
                >
                  {updatingCap ? 'Saving...' : 'Save Capacity'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: DATE RANGE SCHEDULE CREATOR MODAL */}
      {showRangeModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '560px', width: '100%', padding: '2rem' }}>
            <div className="card-header">
              <h3 className="card-title">Date Range Schedule Creator</h3>
            </div>

            <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginBottom: '1.25rem' }}>
              Automatically generate time slots and apply maximum daily quintal intake limits across a range of dates.
              <br />
              <em style={{ color: '#16a34a', fontWeight: 600 }}>Automatically skips closed weekly operating days and holiday exceptions.</em>
            </p>

            <form onSubmit={handleApplyScheduleRange}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">From Date</label>
                  <DateInput 
                    id="range-from-date"
                    value={rangeStartDate}
                    onChange={(newVal) => setRangeStartDate(newVal)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">To Date</label>
                  <DateInput 
                    id="range-to-date"
                    value={rangeEndDate}
                    onChange={(newVal) => setRangeEndDate(newVal)}
                    min={rangeStartDate}
                    required
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label className="form-label">Maximum Quintals Per Day</label>
                <input 
                  type="number"
                  step="1"
                  min="10"
                  className="form-control"
                  value={rangeMaxQuintals}
                  onChange={(e) => setRangeMaxQuintals(e.target.value)}
                  placeholder="e.g. 500"
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label className="form-label">Time Slots (comma-separated)</label>
                <input 
                  type="text"
                  className="form-control"
                  value={rangeTimeSlotsText}
                  onChange={(e) => setRangeTimeSlotsText(e.target.value)}
                  placeholder="09:00 AM - 11:00 AM, 11:00 AM - 01:00 PM"
                  required
                />
              </div>

              <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                <label className="form-label">Max Farmer Capacity Per Time Slot</label>
                <input 
                  type="number"
                  min="1"
                  className="form-control"
                  value={rangeSlotCap}
                  onChange={(e) => setRangeSlotCap(e.target.value)}
                  required
                />
              </div>

              {rangeSummary && (
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', padding: '12px', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem', color: '#166534' }}>
                  <strong>Schedule Generator Summary:</strong>
                  <div>✓ Configured: <strong>{rangeSummary.created_dates_count} operating dates</strong></div>
                  <div>✕ Skipped: <strong>{rangeSummary.skipped_dates_count} closed/holiday dates</strong></div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  style={{ flex: 1 }}
                  onClick={() => {
                    setShowRangeModal(false);
                    setRangeSummary(null);
                  }}
                >
                  Close
                </button>

                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  style={{ flex: 1 }}
                  disabled={generatingSchedule}
                >
                  {generatingSchedule ? 'Generating Schedule...' : 'Generate Schedule Range'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* QR VERIFICATION CAMERA MODAL */}
      {showQrModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '1rem'
        }}>
          <div className="card" style={{ maxWidth: '520px', width: '100%', padding: '2rem', position: 'relative' }}>
            <button 
              onClick={closeQrModal}
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--muted)'
              }}
            >
              <X size={22} />
            </button>

            <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: '50%', backgroundColor: 'var(--primary-light)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.75rem auto' }}>
                <QrCode size={28} />
              </div>
              <h2 style={{ fontSize: '1.4rem', color: 'var(--secondary)' }}>QR Verification</h2>
              <p style={{ fontSize: '0.9rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
                Scan the farmer's procurement pass to verify the appointment.
              </p>
            </div>

            {/* Camera / Processing / Result View Area */}
            {scannerState === 'processing' && (
              <div style={{
                backgroundColor: '#0f172a',
                borderRadius: 'var(--radius-md)',
                minHeight: '220px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem',
                color: 'white',
                padding: '2rem',
                textAlign: 'center'
              }}>
                <div style={{ 
                  width: '38px', 
                  height: '38px', 
                  border: '3px solid rgba(255,255,255,0.2)', 
                  borderTopColor: 'var(--primary)', 
                  borderRadius: '50%', 
                  animation: 'spin 0.8s linear infinite',
                  marginBottom: '1rem'
                }}></div>
                <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', marginBottom: '0.25rem' }}>Processing Verification...</h3>
                <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: 0 }}>Camera stopped. Verifying QR appointment pass.</p>
              </div>
            )}

            {scannerState === 'scanning' && (
              <div style={{
                backgroundColor: '#0f172a',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                minHeight: '230px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1.25rem',
                color: 'white',
                position: 'relative'
              }}>
                <div id="qr-reader" style={{ width: '100%' }}></div>

                {!isCameraActive && (
                  <div style={{ padding: '2rem 1rem', textAlign: 'center' }}>
                    <Camera size={40} style={{ opacity: 0.6, marginBottom: '0.5rem' }} />
                    <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1rem' }}>
                      Camera Scanner is Offline
                    </p>
                    <button 
                      type="button"
                      className="btn btn-primary"
                      onClick={startCameraScanner}
                    >
                      <Camera size={18} /> ACTIVATE CAMERA
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Verification Result Card - REPLACES the camera view completely */}
            {scannerState === 'result' && verificationResult && (
              <div style={{
                padding: '1.25rem',
                borderRadius: 'var(--radius-md)',
                marginBottom: '1.25rem',
                backgroundColor: verificationResult.success ? 'var(--success-bg)' : 'var(--danger-bg)',
                border: `1.5px solid ${verificationResult.success ? 'var(--primary-border)' : '#fca5a5'}`,
                color: verificationResult.success ? 'var(--success-text)' : 'var(--danger-text)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>
                    {verificationResult.success ? 'VERIFIED ✓' : (verificationResult.error || 'INVALID QR CODE ✕')}
                  </h3>
                  <span className={`badge ${verificationResult.success ? 'badge-confirmed' : 'badge-rejected'}`}>
                    {verificationResult.success ? 'VERIFIED' : 'INVALID'}
                  </span>
                </div>

                <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: verificationResult.appointment ? '0.75rem' : '1rem' }}>
                  {verificationResult.message}
                </p>

                {verificationResult.appointment && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem', backgroundColor: 'white', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', color: 'var(--secondary)', marginBottom: '1rem' }}>
                    <div><strong>Farmer:</strong> {verificationResult.appointment.farmer_name}</div>
                    <div><strong>Appointment ID:</strong> {verificationResult.appointment.appointment_id}</div>
                    <div><strong>Crop:</strong> {verificationResult.appointment.crop}</div>
                    <div><strong>Quantity:</strong> {verificationResult.appointment.quantity} Quintals</div>
                    <div><strong>Date:</strong> {formatDateDisplay(verificationResult.appointment.date)}</div>
                    <div><strong>Time Slot:</strong> {verificationResult.appointment.time_slot}</div>
                  </div>
                )}

                <button 
                  type="button"
                  className="btn btn-primary"
                  style={{ width: '100%', marginTop: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                  onClick={handleScanAnotherQr}
                >
                  <QrCode size={18} /> Verify Another QR Code
                </button>
              </div>
            )}

            {/* Manual Appointment ID / QR Code Input */}
            <div style={{ paddingTop: '1rem', borderTop: '1px solid var(--border)' }}>
              <label className="form-label" style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--muted)' }}>
                Manual Verification (Desktop / Scanner Input)
              </label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input 
                  type="text"
                  className="form-control"
                  placeholder="Enter Appointment ID (e.g. PF-260915-001)"
                  value={manualToken}
                  onChange={(e) => setManualToken(e.target.value)}
                />
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={() => handleVerifyToken(manualToken)}
                  disabled={!manualToken.trim() || verifying}
                >
                  Verify
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
