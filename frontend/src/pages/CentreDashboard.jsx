import React, { useEffect, useState, useRef, useCallback } from 'react';
import { 
  getCentreBookings, 
  updateBookingStatus, 
  getSlots, 
  createSlot, 
  updateSlotCapacity, 
  deleteSlot, 
  verifyQrToken,
  getOperatingConfig,
  updateOperatingConfig,
  updateOperatingDays,
  addNonOperationalDate,
  removeNonOperationalDate,
  getDailyCapacity,
  updateDailyCapacity,
  applyScheduleRange,
  recordCollection,
  recordQualityCheck,
  recordWeighment,
  recordProcurement,
  completePayment,
  getCentreOperationalIntelligence,
  getEstimatedPrice,
  uploadProcurementEvidence,
  getProcurementEvidence,
  getCentreAlerts,
  getCentreInsights,
  getCentreDailyIntelligence,
  getCentreRedirectionOptions,
  resolveAlert,
  getCentreEmployees,
  addCentreEmployee,
  deleteCentreEmployee,
  getLiveQueue,
  getCongestionForecast,
  queryCentreCopilot
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
  ChevronDown,
  ChevronUp,
  ListFilter,
  Wheat,
  Brain,
  Truck,
  Package,
  Activity,
  AlertTriangle,
  Image as ImageIcon,
  Upload,
  Droplets,
  FileCheck,
  Eye,
  Warehouse,
  UserPlus,
  RefreshCw,
  Route,
  Sparkles,
  MessageSquare,
  Bot,
  CheckCircle,
  XCircle,
  BarChart3,
  Code
} from 'lucide-react';
import { formatDateDisplay } from '../utils/dateUtils';
import DateInput from '../components/DateInput';
import ErrorBoundary from '../components/ErrorBoundary';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function CentreDashboard({ user, navigate, initialTab = 'overview' }) {
  // Navigation tab state: 'overview' | 'appointments' | 'slots' | 'config'
  const [activeTab, setActiveTab] = useState(initialTab || 'overview');

  useEffect(() => {
    if (initialTab && initialTab !== activeTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  // Resolve the correct centre identifier from the token
  // The token stores centre_id when the logged-in user is a centre manager
  const centreId = user?.centre_id || user?.user_id;

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

  // Live Queue & SIH Congestion Forecast (Requirements 8, 15, 16)
  const resolvedCentreId = centreId;
  const [sihLiveQueue, setSihLiveQueue] = useState(null);
  const [sihCongestion, setSihCongestion] = useState(null);
  const [loadingSihQueue, setLoadingSihQueue] = useState(false);

  const fetchSihQueueData = useCallback(() => {
    if (!centreId) return;
    setLoadingSihQueue(true);
    Promise.all([
      getLiveQueue(centreId).catch(() => null),
      getCongestionForecast(centreId).catch(() => null)
    ])
      .then(([qData, cData]) => {
        setSihLiveQueue(qData);
        setSihCongestion(cData);
      })
      .finally(() => setLoadingSihQueue(false));
  }, [centreId]);

  useEffect(() => {
    fetchSihQueueData();
  }, [fetchSihQueueData]);

  // Centre Copilot State (Isolated Mandi Sahayak - Requirement 38)
  const [centreCopilotQuery, setCentreCopilotQuery] = useState('');
  const [centreCopilotLoading, setCentreCopilotLoading] = useState(false);
  const [centreCopilotResponse, setCentreCopilotResponse] = useState(null);
  const [centreCopilotContext, setCentreCopilotContext] = useState(null);
  const [showCentreCopilotDebug, setShowCentreCopilotDebug] = useState(false);
  const [centreCopilotError, setCentreCopilotError] = useState(null);
  const [centreCopilotLastQuery, setCentreCopilotLastQuery] = useState('');

  const handleAskCentreCopilot = async (customPrompt) => {
    const q = customPrompt || centreCopilotQuery;
    if (!q || !q.trim()) return;
    const queryStr = q.trim();
    setCentreCopilotLastQuery(queryStr);
    setCentreCopilotLoading(true);
    setCentreCopilotError(null);
    setCentreCopilotResponse(null);
    try {
      const res = await queryCentreCopilot(resolvedCentreId || centreId, queryStr, centreCopilotContext);
      if (!res) {
        throw new Error('Received empty response from Centre Copilot service.');
      }
      setCentreCopilotResponse({
        ...res,
        answer: res.answer || 'No records found matching your centre query criteria.'
      });
      if (res && res.session_context) {
        setCentreCopilotContext(res.session_context);
      }
    } catch (err) {
      console.error('[Centre Copilot Error]:', err);
      const errMsg = err?.response?.data?.detail || err.message || 'Failed to communicate with Centre Copilot service.';
      setCentreCopilotError(errMsg);
      setCentreCopilotResponse({ answer: 'Centre Copilot query failed: ' + errMsg });
    } finally {
      setCentreCopilotLoading(false);
    }
  };

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

  // Arrived Farmer Procurement Modal State
  const [selectedArrivedBooking, setSelectedArrivedBooking] = useState(null);
  const [procurementForm, setProcurementForm] = useState({
    actual_quantity: '',
    actual_weight: '',
    quality_grade: 'GRADE_A',
    moisture_pct: '12.0',
    warehouse_location: 'Bay A-1',
    notes: '',
    payment_amount: ''
  });
  const [procurementStep, setProcurementStep] = useState('received'); // 'received' | 'quality' | 'weighment' | 'storage' | 'payment' | 'complete'
  const [workflowRecordIds, setWorkflowRecordIds] = useState({
    collection_id: null,
    check_id: null,
    weighment_id: null,
    payment_id: null
  });
  const [submittingProcurement, setSubmittingProcurement] = useState(false);
  const [procurementError, setProcurementError] = useState('');

  // Photo Evidence State (Quality, Weighing, Moisture)
  const [bookingEvidence, setBookingEvidence] = useState({ QUALITY: [], WEIGHING: [], MOISTURE: [] });
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [evidenceUploadStatus, setEvidenceUploadStatus] = useState({
    QUALITY: { uploading: false, error: '', success: '' },
    WEIGHING: { uploading: false, error: '', success: '' },
    MOISTURE: { uploading: false, error: '', success: '' }
  });
  const [pendingFiles, setPendingFiles] = useState({
    QUALITY: null,
    WEIGHING: null,
    MOISTURE: null
  });
  const [filePreviews, setFilePreviews] = useState({
    QUALITY: null,
    WEIGHING: null,
    MOISTURE: null
  });
  const [enlargedImage, setEnlargedImage] = useState(null);

  const loadBookingEvidence = async (numericBookingId) => {
    if (!numericBookingId) return;
    setLoadingEvidence(true);
    try {
      const res = await getProcurementEvidence(numericBookingId);
      if (res && res.by_type) {
        setBookingEvidence({
          QUALITY: res.by_type.QUALITY || [],
          WEIGHING: res.by_type.WEIGHING || [],
          MOISTURE: res.by_type.MOISTURE || []
        });
      }
    } catch (e) {
      console.warn('Could not load evidence for booking:', e);
    } finally {
      setLoadingEvidence(false);
    }
  };

  const handleSelectEvidenceFile = (type, file) => {
    if (!file) return;
    const allowed = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!allowed.includes(file.type.toLowerCase())) {
      setEvidenceUploadStatus(prev => ({
        ...prev,
        [type]: { uploading: false, error: 'Only JPG, PNG, and WEBP images are supported.', success: '' }
      }));
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setEvidenceUploadStatus(prev => ({
        ...prev,
        [type]: { uploading: false, error: 'File size must be 5MB or less.', success: '' }
      }));
      return;
    }

    if (filePreviews[type]) {
      try { URL.revokeObjectURL(filePreviews[type]); } catch (e) {}
    }
    const previewUrl = URL.createObjectURL(file);
    setPendingFiles(prev => ({ ...prev, [type]: file }));
    setFilePreviews(prev => ({ ...prev, [type]: previewUrl }));
    setEvidenceUploadStatus(prev => ({
      ...prev,
      [type]: { uploading: false, error: '', success: '' }
    }));
  };

  const handleClearPendingFile = (type) => {
    if (filePreviews[type]) {
      try { URL.revokeObjectURL(filePreviews[type]); } catch (e) {}
    }
    setPendingFiles(prev => ({ ...prev, [type]: null }));
    setFilePreviews(prev => ({ ...prev, [type]: null }));
    setEvidenceUploadStatus(prev => ({
      ...prev,
      [type]: { uploading: false, error: '', success: '' }
    }));
  };

  const handleUploadSingleEvidence = async (type, numericBookingId) => {
    const file = pendingFiles[type];
    if (!file || !numericBookingId) return;

    setEvidenceUploadStatus(prev => ({
      ...prev,
      [type]: { uploading: true, error: '', success: '' }
    }));

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('booking_id', String(numericBookingId));
      formData.append('evidence_type', type);
      formData.append('notes', `${type} photo measurement captured at mandi`);

      const res = await uploadProcurementEvidence(formData);
      if (res.success) {
        handleClearPendingFile(type);
        setEvidenceUploadStatus(prev => ({
          ...prev,
          [type]: { uploading: false, error: '', success: `${type} photo uploaded successfully!` }
        }));
        await loadBookingEvidence(numericBookingId);
      } else {
        throw new Error(res.message || 'Upload failed');
      }
    } catch (err) {
      setEvidenceUploadStatus(prev => ({
        ...prev,
        [type]: { uploading: false, error: err.message || 'Failed to upload photo', success: '' }
      }));
    }
  };

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

  // Operational Intelligence State (AI / Predictive Logistics)
  const [opIntelligence, setOpIntelligence] = useState(null);

  // Iteration 2 Intelligence States
  const [centreAlerts, setCentreAlerts] = useState([]);
  const [centreInsights, setCentreInsights] = useState(null);
  const [centreDailyIntel, setCentreDailyIntel] = useState(null);
  const [redirectionOptions, setRedirectionOptions] = useState(null);
  const [alertFilter, setAlertFilter] = useState('ALL');
  const [resolvingAlertId, setResolvingAlertId] = useState(null);

  // Employee Management State for Tab 4 (Configure Days)
  const [employees, setEmployees] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [newEmpForm, setNewEmpForm] = useState({
    name: '',
    role: 'Intake Officer',
    employee_code: '',
    phone: '',
    email: ''
  });
  const [addingEmp, setAddingEmp] = useState(false);
  const [empError, setEmpError] = useState('');
  const [empSuccess, setEmpSuccess] = useState('');

  // Expandable Insights State (Requirement 6)
  const [expandedInsights, setExpandedInsights] = useState({});
  const toggleInsight = (key) => {
    setExpandedInsights(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const loadEmployees = async () => {
    if (!centreId) return;
    setLoadingEmployees(true);
    try {
      const res = await getCentreEmployees(centreId);
      if (res && res.employees) {
        setEmployees(res.employees);
      }
    } catch (e) {
      console.warn('Could not load employees:', e);
    } finally {
      setLoadingEmployees(false);
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    setEmpError('');
    setEmpSuccess('');
    if (!newEmpForm.name.trim()) {
      setEmpError('Employee name is required.');
      return;
    }
    setAddingEmp(true);
    try {
      const code = newEmpForm.employee_code.trim() || `EMP-${Date.now().toString().slice(-4)}`;
      const payload = {
        name: newEmpForm.name.trim(),
        role: newEmpForm.role,
        employee_code: code,
        phone: newEmpForm.phone.trim() || '9876543210',
        email: newEmpForm.email.trim() || `${code.toLowerCase()}@bharatagri.gov.in`
      };
      const res = await addCentreEmployee(centreId, payload);
      if (res && res.success) {
        setEmpSuccess(`Employee ${payload.name} (${payload.employee_code}) added successfully!`);
        setNewEmpForm({
          name: '',
          role: 'Intake Officer',
          employee_code: '',
          phone: '',
          email: ''
        });
        await loadEmployees();
      }
    } catch (err) {
      setEmpError(err.message || 'Failed to add employee.');
    } finally {
      setAddingEmp(false);
    }
  };

  const handleDeleteEmployee = async (empId, empName) => {
    if (!window.confirm(`Deactivate employee "${empName}" from centre roster?`)) return;
    setEmpError('');
    setEmpSuccess('');
    try {
      await deleteCentreEmployee(centreId, empId);
      setEmpSuccess(`Employee "${empName}" deactivated.`);
      await loadEmployees();
    } catch (err) {
      setEmpError(err.message || 'Failed to deactivate employee.');
    }
  };

  const loadCentreData = () => {
    if (user && centreId) {
      setLoading(true);
      Promise.all([
        getCentreBookings(centreId, selectedDate).catch(() => []),
        getSlots(centreId, selectedDate).catch(() => []),
        getOperatingConfig(centreId).catch(() => null),
        getDailyCapacity(centreId, selectedDate).catch(() => null),
        getCentreOperationalIntelligence(centreId).catch(() => null),
        getCentreAlerts(centreId).catch(() => []),
        getCentreInsights(centreId).catch(() => null),
        getCentreDailyIntelligence(centreId).catch(() => null),
        getCentreRedirectionOptions(centreId).catch(() => null),
        getCentreEmployees(centreId).catch(() => ({ employees: [] }))
      ])
        .then(([bookingsData, slotsData, configData, capData, intelData, alertsData, insightsData, dailyData, redirData, empsData]) => {
          setBookings(Array.isArray(bookingsData) ? bookingsData : []);
          setSlots(Array.isArray(slotsData) ? slotsData : []);
          setOperatingDays(parseDaysArray(configData?.operating_days));
          setNonOperationalDates(configData?.non_operational_dates || []);
          setDailyCapacityInfo(capData || { max_quintals_per_day: 500, booked_quintals: 0, available_quintals: 500 });
          setEditDailyQuintalVal(capData?.max_quintals_per_day || 500);
          if (intelData?.intelligence) {
            setOpIntelligence(intelData.intelligence);
          }
          setCentreAlerts(Array.isArray(alertsData) ? alertsData : (alertsData?.alerts || []));
          setCentreInsights(insightsData);
          setCentreDailyIntel(dailyData);
          setRedirectionOptions(redirData);
          setEmployees(empsData?.employees || []);
        })
        .catch(err => setError('Failed to load centre data: ' + (err.message || '')))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    if (resolvingAlertId) return;
    setResolvingAlertId(alertId);
    try {
      await resolveAlert(alertId);
      setSuccessMsg(`Alert #${alertId} marked as resolved.`);
      setCentreAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'RESOLVED' } : a));
    } catch (e) {
      setError('Failed to resolve alert: ' + (e.message || ''));
    } finally {
      setResolvingAlertId(null);
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

  const handleOpenProcurementModal = async (b) => {
    setSelectedArrivedBooking(b);
    setWorkflowRecordIds({ collection_id: null, check_id: null, weighment_id: null, payment_id: null });
    const rawBkId = b.id !== undefined && b.id !== null ? b.id : b.booking_id;
    const numBkId = typeof rawBkId === 'number' ? rawBkId : parseInt(rawBkId, 10);
    setPendingFiles({ QUALITY: null, WEIGHING: null, MOISTURE: null });
    setFilePreviews({ QUALITY: null, WEIGHING: null, MOISTURE: null });
    setEvidenceUploadStatus({
      QUALITY: { uploading: false, error: '', success: '' },
      WEIGHING: { uploading: false, error: '', success: '' },
      MOISTURE: { uploading: false, error: '', success: '' }
    });
    if (!isNaN(numBkId) && numBkId > 0) {
      loadBookingEvidence(numBkId);
    }
    const qty = parseFloat(b.quantity || 1);
    let msp = 2300;
    let estPrice = 2345;
    try {
      const pRes = await getEstimatedPrice({ crop: b.crop, quantity: qty, centre_id: centreId });
      if (pRes) {
        msp = pRes.official_msp || 2300;
        estPrice = pRes.estimated_price || 2345;
      }
    } catch (e) {
      console.warn("Price lookup fallback", e);
    }

    setProcurementForm({
      actual_quantity: b.quantity || '',
      actual_weight: b.quantity || '',
      quality_grade: 'GRADE_A',
      moisture_pct: '12.0',
      warehouse_location: 'Bay A-1',
      notes: 'Initial receipt and moisture inspection verified at mandi.',
      official_msp: msp,
      estimated_price: estPrice,
      msp_reference_value: (qty * msp).toFixed(2),
      estimated_value: (qty * estPrice).toFixed(2),
      payment_amount: (qty * estPrice).toFixed(2)
    });

    if (b.status === 'ARRIVED' || b.status === 'VERIFIED' || b.status === 'BOOKED' || b.status === 'CONFIRMED') {
      setProcurementStep('received');
    } else if (b.status === 'RECEIVED') {
      setProcurementStep('quality');
    } else if (b.status === 'QUALITY_CHECKED') {
      setProcurementStep('weighment');
    } else if (b.status === 'WEIGHED') {
      setProcurementStep('storage');
    } else if (b.status === 'STORED' || b.status === 'PAYMENT_INITIATED') {
      setProcurementStep('payment');
    } else if (b.status === 'PAID') {
      setProcurementStep('complete');
    } else {
      setProcurementStep('received');
    }
    setProcurementError('');
  };

  const handleProcessWorkflowStep = async (targetStatus) => {
    if (!selectedArrivedBooking) return;
    
    // Resolve actual numeric booking ID (existing database primary key)
    const rawBookingId = selectedArrivedBooking.id !== undefined && selectedArrivedBooking.id !== null
      ? selectedArrivedBooking.id
      : selectedArrivedBooking.booking_id;
    const numericBookingId = typeof rawBookingId === 'number' ? rawBookingId : parseInt(rawBookingId, 10);

    if (isNaN(numericBookingId) || numericBookingId <= 0) {
      setProcurementError('Invalid booking record: Missing or non-numeric database booking ID.');
      return;
    }

    const appointmentDisplay = selectedArrivedBooking.appointment_id || `Booking #${numericBookingId}`;
    setSubmittingProcurement(true);
    setProcurementError('');
    try {
      if (targetStatus === 'RECEIVED') {
        const colRes = await recordCollection({
          booking_id: numericBookingId,
          farmer_id: selectedArrivedBooking.farmer_id || selectedArrivedBooking.farmer_name,
          centre_id: centreId,
          crop: selectedArrivedBooking.crop,
          collected_quantity: parseFloat(procurementForm.actual_quantity || selectedArrivedBooking.quantity),
          gross_weight_quintals: parseFloat(procurementForm.actual_weight || selectedArrivedBooking.quantity),
          collected_by: user?.name || 'Procurement Staff'
        });
        const colId = colRes?.collection_id || colRes?.data?.collection_id;
        if (colId) {
          setWorkflowRecordIds(prev => ({ ...prev, collection_id: colId }));
        }
        setProcurementStep('quality');
      } else if (targetStatus === 'QUALITY_CHECKED') {
        // Auto-upload optional quality & moisture evidence if selected
        if (pendingFiles.QUALITY) {
          try { await handleUploadSingleEvidence('QUALITY', numericBookingId); } catch (e) { console.warn(e); }
        }
        if (pendingFiles.MOISTURE) {
          try { await handleUploadSingleEvidence('MOISTURE', numericBookingId); } catch (e) { console.warn(e); }
        }
        const qcRes = await recordQualityCheck({
          collection_id: workflowRecordIds.collection_id || undefined,
          booking_id: numericBookingId,
          quality_grade: procurementForm.quality_grade,
          moisture_content_pct: parseFloat(procurementForm.moisture_pct || 12.0),
          foreign_matter_pct: 1.2,
          broken_grains_pct: 0.5,
          damaged_grains_pct: 0.2,
          inspector_name: user?.name || 'Inspector',
          passed: true,
          notes: procurementForm.notes
        });
        const qId = qcRes?.check_id || qcRes?.data?.check_id;
        if (qId) {
          setWorkflowRecordIds(prev => ({ ...prev, check_id: qId }));
        }
        setProcurementStep('weighment');
      } else if (targetStatus === 'WEIGHED') {
        // Auto-upload optional weighing evidence if selected
        if (pendingFiles.WEIGHING) {
          try { await handleUploadSingleEvidence('WEIGHING', numericBookingId); } catch (e) { console.warn(e); }
        }
        const gross = parseFloat(procurementForm.actual_weight || procurementForm.actual_quantity || selectedArrivedBooking.quantity);
        const tare = 0.5;
        const wbRes = await recordWeighment({
          collection_id: workflowRecordIds.collection_id || undefined,
          quality_check_id: workflowRecordIds.check_id || undefined,
          booking_id: numericBookingId,
          gross_weight_quintals: gross + tare,
          tare_weight_quintals: tare,
          operator_name: user?.name || 'Scale Operator'
        });
        const wbId = wbRes?.weighment_id || wbRes?.data?.weighment_id;
        if (wbId) {
          setWorkflowRecordIds(prev => ({ ...prev, weighment_id: wbId }));
        }
        setProcurementStep('storage');
      } else if (targetStatus === 'STORED') {
        const procRes = await recordProcurement({
          booking_id: numericBookingId,
          collection_id: workflowRecordIds.collection_id || undefined,
          weighment_id: workflowRecordIds.weighment_id || undefined,
          farmer_id: selectedArrivedBooking.farmer_id || selectedArrivedBooking.farmer_name,
          centre_id: centreId,
          crop: selectedArrivedBooking.crop,
          procured_quantity_quintals: parseFloat(procurementForm.actual_weight || selectedArrivedBooking.quantity),
          rate_per_quintal_inr: parseFloat(procurementForm.official_msp || 2300),
          warehouse_location: procurementForm.warehouse_location
        });
        const payId = procRes?.payment_id || procRes?.data?.payment_id;
        if (payId) {
          setWorkflowRecordIds(prev => ({ ...prev, payment_id: payId }));
        }
        setProcurementStep('payment');
      } else if (targetStatus === 'PAID') {
        if (workflowRecordIds.payment_id) {
          await completePayment(workflowRecordIds.payment_id);
        } else {
          await updateBookingStatus(selectedArrivedBooking.appointment_id || String(numericBookingId), 'PAID');
        }
        setProcurementStep('complete');
      }

      setSuccessMsg(`Workflow updated to ${targetStatus} for ${appointmentDisplay}!`);
      
      // Update local booking status immediately
      setBookings(prev => prev.map(item => {
        const match = item.id === numericBookingId || item.appointment_id === selectedArrivedBooking.appointment_id;
        return match ? { ...item, status: targetStatus } : item;
      }));

      loadCentreData();
    } catch (err) {
      setProcurementError(err.message || `Failed to process ${targetStatus}`);
    } finally {
      setSubmittingProcurement(false);
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
      const res = await verifyQrToken(tokenToVerify.trim(), centreId);
      setVerificationResult(res);
      setScannerState('result');
      if (res.success) {
        loadCentreData();
      }
    } catch (err) {
      setVerificationResult({
        success: false,
        code: 'ERROR',
        error: 'INVALID QR CODE',
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

  async function stopCameraScanner() {
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

  const renderEvidenceSection = (type, title, description) => {
    const rawBkId = selectedArrivedBooking?.id ?? selectedArrivedBooking?.booking_id;
    const currentBookingId = typeof rawBkId === 'number' ? rawBkId : parseInt(rawBkId, 10);
    const existingList = bookingEvidence[type] || [];
    const pendingFile = pendingFiles[type];
    const previewUrl = filePreviews[type];
    const status = evidenceUploadStatus[type];

    return (
      <div className="evidence-section" style={{
        marginTop: '0.75rem',
        padding: '0.85rem',
        borderRadius: 'var(--radius-sm)',
        background: 'var(--bg-page)',
        border: '1px solid var(--border)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div>
            <strong style={{ fontSize: '0.85rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ImageIcon size={15} style={{ color: 'var(--primary)' }} />
              {title}
            </strong>
            <span style={{ fontSize: '0.75rem', color: 'var(--muted)', display: 'block' }}>
              {description} <em style={{ fontStyle: 'normal', color: 'var(--primary)', fontWeight: 600 }}>(Optional)</em>
            </span>
          </div>
          {existingList.length > 0 && (
            <span className="badge badge-confirmed" style={{ fontSize: '0.7rem' }}>
              <FileCheck size={12} style={{ marginRight: '4px' }} /> {existingList.length} Uploaded
            </span>
          )}
        </div>

        {/* Existing uploaded evidence thumbnails */}
        {existingList.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
            {existingList.map((ev, idx) => (
              <div 
                key={ev.id || idx}
                style={{
                  position: 'relative',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-sm)',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  background: 'var(--bg-card)'
                }}
                onClick={() => setEnlargedImage(ev.file_path || ev.file_url)}
                title="Click to enlarge"
              >
                <img 
                  src={ev.file_path || ev.file_url} 
                  alt={ev.original_filename || `${type} Evidence`} 
                  style={{ width: '70px', height: '70px', objectFit: 'cover', display: 'block' }}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  right: 0,
                  background: 'rgba(0,0,0,0.6)',
                  color: '#fff',
                  fontSize: '0.62rem',
                  padding: '2px 4px',
                  textAlign: 'center',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                  whiteSpace: 'nowrap'
                }}>
                  {ev.original_filename || `Evidence #${idx+1}`}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.75rem', color: 'var(--muted)', fontStyle: 'italic', marginBottom: '0.5rem' }}>
            No evidence uploaded yet
          </div>
        )}

        {/* File selection & preview */}
        {previewUrl ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            padding: '0.5rem',
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--primary-border)',
            marginBottom: '0.5rem'
          }}>
            <img 
              src={previewUrl} 
              alt="Selected Preview" 
              style={{ width: '56px', height: '56px', objectFit: 'cover', borderRadius: '4px', border: '1px solid var(--border)' }}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {pendingFile?.name}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                {(pendingFile?.size / 1024).toFixed(1)} KB • Ready to save
              </div>
            </div>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button
                type="button"
                className="btn btn-primary"
                style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                disabled={status.uploading}
                onClick={() => handleUploadSingleEvidence(type, currentBookingId)}
              >
                {status.uploading ? 'Uploading...' : 'Upload Now'}
              </button>
              <button
                type="button"
                className="btn btn-outline"
                style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                onClick={() => handleClearPendingFile(type)}
                disabled={status.uploading}
              >
                <X size={14} />
              </button>
            </div>
          </div>
        ) : (
          <label style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '6px 12px',
            borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--border)',
            background: 'var(--bg-card)',
            color: 'var(--secondary)',
            fontSize: '0.78rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}>
            <Upload size={14} style={{ color: 'var(--primary)' }} />
            <span>Select {title.split(' ')[0]} Photo (JPG/PNG/WEBP, Max 5MB)</span>
            <input 
              type="file" 
              accept="image/jpeg,image/png,image/webp" 
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  handleSelectEvidenceFile(type, e.target.files[0]);
                }
              }}
            />
          </label>
        )}

        {/* Status messages */}
        {status.error && (
          <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--danger-text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <AlertTriangle size={13} /> {status.error}
          </div>
        )}
        {status.success && (
          <div style={{ marginTop: '0.4rem', fontSize: '0.75rem', color: 'var(--success-text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle size={13} /> {status.success}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="centre-dashboard animate-fade-in">
      {/* Top Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', color: 'var(--secondary)' }}>
            Welcome, {user?.name || 'Centre Manager'}
          </h1>
          <p style={{ fontSize: '0.95rem', color: 'var(--muted)' }}>Procurement Centre Management & Date-based Portal</p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button 
            className="btn btn-primary btn-lg"
            onClick={openQrModal}
            style={{ boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <QrCode size={20} /> QR VERIFICATION
          </button>
          <button 
            className="btn btn-outline btn-lg"
            onClick={() => {
              setActiveTab('copilot');
              window.location.hash = 'copilot';
            }}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700 }}
          >
            <Sparkles size={18} color="var(--primary)" /> Ask Copilot
          </button>
        </div>
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
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--secondary)' }}>
              {user?.centre_name ? `${user.centre_name} (${user.name})` : (user?.name || 'Procurement Centre')}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--info-bg)', color: 'var(--info-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Clock size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>CENTRE ID</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--secondary)' }}>
              {centreId || user?.centre_id || user?.user_id}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: 'var(--success-bg)', color: 'var(--success-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Scale size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>DAILY QUINTAL INTAKE CAP</div>
            <div style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary)' }}>
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

        <button 
          className={`btn ${activeTab === 'alerts' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('alerts')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px', position: 'relative' }}
        >
          <AlertTriangle size={18} /> Alerts
          {centreAlerts.filter(a => a.status === 'ACTIVE').length > 0 && (
            <span style={{
              background: '#ef4444',
              color: '#fff',
              fontSize: '0.7rem',
              fontWeight: 800,
              padding: '1px 6px',
              borderRadius: '999px',
              marginLeft: '4px'
            }}>
              {centreAlerts.filter(a => a.status === 'ACTIVE').length}
            </span>
          )}
        </button>

        <button 
          className={`btn ${activeTab === 'insights' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('insights')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Brain size={18} /> Centre Insights
        </button>

        <button 
          className={`btn ${activeTab === 'copilot' ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => setActiveTab('copilot')}
          style={{ borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Sparkles size={18} /> Centre Copilot
        </button>
      </div>

      {/* UNIVERSAL TOP DATE SELECTION CONTROL (Applies across Overview, Appointments, and Schedule Editor) */}
      <div className="card shadow-sm mb-4" style={{ padding: '16px 24px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px' }}>
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

          <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--info-text)', background: 'var(--info-bg)', padding: '6px 14px', borderRadius: '20px' }}>
            Selected Date: {formatDateDisplay(selectedDate)}
          </div>
        </div>
      </div>

      {/* TAB 1: DATE-BASED OVERVIEW & CROP SUMMARY */}
      {activeTab === 'overview' && (
        <>
          {/* SIH DYNAMIC AI LIVE QUEUE & HOURLY CONGESTION FORECAST (Requirements 8, 15, 16) */}
          <div className="congestion-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '50%', background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' }}>
                  <Activity size={18} />
                </span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Live Queue Operations & Hourly Congestion Forecast
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                    {sihLiveQueue?.centre_name || resolvedCentreId} • Last updated {sihLiveQueue?.last_updated || 'Live'}
                  </span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{
                  padding: '4px 12px', borderRadius: '999px', fontSize: '0.78rem', fontWeight: 800,
                  backgroundColor: sihLiveQueue?.status_color === 'warning' ? 'var(--warning-bg)' : 'var(--success-bg)',
                  color: sihLiveQueue?.status_color === 'warning' ? 'var(--warning-text)' : 'var(--success-text)',
                  border: '1px solid currentColor',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px'
                }}>
                  <CheckCircle size={12} /> {sihLiveQueue?.status_label?.replace(/^[^a-zA-Z0-9]+/, '') || 'Centre operating normally'}
                </span>
                <button
                  onClick={fetchSihQueueData}
                  disabled={loadingSihQueue}
                  className="btn btn-outline"
                  style={{ padding: '4px 10px', fontSize: '0.75rem', color: 'var(--secondary)', borderColor: 'var(--border)' }}
                >
                  <RefreshCw size={12} className={loadingSihQueue ? 'animate-spin' : ''} /> Refresh
                </button>
              </div>
            </div>

            {/* 5 Real KPI Numbers from SIH Queue Events */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px', marginBottom: '16px' }}>
              <div className="briefing-stat-card">
                <span className="briefing-stat-label">Farmers Waiting</span>
                <div className="briefing-stat-value" style={{ color: 'var(--secondary)' }}>
                  {sihLiveQueue?.queue_length ?? 0}
                </div>
                <span style={{ fontSize: '0.7rem', color: '#0284c7', fontWeight: 600 }}>In Mandi Yard</span>
              </div>

              <div className="briefing-stat-card">
                <span className="briefing-stat-label">Serving Token</span>
                <div className="briefing-stat-value" style={{ color: '#d97706' }}>
                  {sihLiveQueue?.current_serving_token ?? '--'}
                </div>
                <span style={{ fontSize: '0.7rem', color: '#d97706', fontWeight: 600 }}>At Weighbridge WB-01</span>
              </div>

              <div className="briefing-stat-card">
                <span className="briefing-stat-label">ML Predicted Wait</span>
                <div className="briefing-stat-value" style={{ color: 'var(--danger-text)' }}>
                  {sihLiveQueue?.estimated_wait_min ?? 0} <span style={{ fontSize: '0.9rem' }}>min</span>
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>Baseline: {sihLiveQueue?.baseline_wait_min ?? 0} min</span>
              </div>

              <div className="briefing-stat-card">
                <span className="briefing-stat-label">Active Weigh Stations</span>
                <div className="briefing-stat-value" style={{ color: 'var(--success-text)' }}>
                  {sihLiveQueue?.active_stations ?? opIntelligence?.infrastructure?.weighbridges_active ?? 0} / {opIntelligence?.infrastructure?.weighbridges_total ?? 3}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--success-text)', fontWeight: 600 }}>Operational</span>
              </div>

              <div className="briefing-stat-card">
                <span className="briefing-stat-label">Processing Rate</span>
                <div className="briefing-stat-value" style={{ color: 'var(--secondary)' }}>
                  {sihLiveQueue?.processing_rate_farmers_per_hour ?? 0} <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>/hr</span>
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>Avg {sihLiveQueue?.avg_processing_time_min ?? 0} min/farmer</span>
              </div>
            </div>

            {/* HOURLY CONGESTION FORECAST (Requirement 15) */}
            {sihCongestion?.hourly_forecast && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--secondary)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <BarChart3 size={15} /> Hourly Congestion Forecast (Today 8 AM – 5 PM)
                  </span>
                  {sihCongestion.high_congestion_alert && (
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--danger-text)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <AlertTriangle size={12} /> Peak congestion window: {sihCongestion.peak_hours_window}
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(85px, 1fr))', gap: '8px' }}>
                  {sihCongestion.hourly_forecast.map((h, i) => {
                    const isCritical = h.congestion_level === 'CRITICAL';
                    const isHigh = h.congestion_level === 'HIGH';
                    return (
                      <div
                        key={i}
                        className={`congestion-hour-cell ${isCritical ? 'critical' : isHigh ? 'high' : 'normal'}`}
                      >
                        <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{h.display_time}</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 900, color: isCritical ? 'var(--danger-text)' : isHigh ? 'var(--warning-text)' : 'var(--secondary)', margin: '2px 0' }}>
                          {h.predicted_arrivals}
                        </div>
                        <span style={{
                          fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
                          color: isCritical ? 'var(--danger-text)' : isHigh ? 'var(--warning-text)' : 'var(--success-text)'
                        }}>
                          {h.congestion_level}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          {/* DAILY INTELLIGENCE EXECUTIVE SUMMARY (Requirement 11) */}
          {centreDailyIntel?.daily_intelligence && (
            <div className="briefing-card">
              <div className="briefing-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6366f1' }}>
                    <Activity size={20} />
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: 'var(--secondary)' }}>
                      Centre Daily Intelligence Briefing
                    </h3>
                    <span style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                      Operational forecasts for {centreDailyIntel.centre_name || 'Procurement Centre'} • {formatDateDisplay(selectedDate)}
                    </span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={{
                    padding: '4px 10px',
                    borderRadius: '999px',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    background: centreDailyIntel.daily_intelligence.capacity_forecast?.capacity_status === 'CRITICAL' ? 'var(--danger-bg)' : 'var(--success-bg)',
                    color: centreDailyIntel.daily_intelligence.capacity_forecast?.capacity_status === 'CRITICAL' ? 'var(--danger-text)' : 'var(--success-text)',
                    border: '1px solid currentColor'
                  }}>
                    Capacity: {centreDailyIntel.daily_intelligence.capacity_forecast?.capacity_status || 'NORMAL'}
                  </span>
                  {centreDailyIntel.daily_intelligence.active_alerts_count > 0 && (
                    <button
                      onClick={() => setActiveTab('alerts')}
                      style={{
                        padding: '4px 12px',
                        borderRadius: '999px',
                        fontSize: '0.72rem',
                        fontWeight: 700,
                        background: 'var(--danger)',
                        color: '#fff',
                        border: 'none',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      <AlertTriangle size={12} /> {centreDailyIntel.daily_intelligence.active_alerts_count} Active Alerts
                    </button>
                  )}
                </div>
              </div>

              {/* 4 Key Intelligence Metrics */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                <div className="briefing-stat-card">
                  <span className="briefing-stat-label">Expected Arrivals Today</span>
                  <div className="briefing-stat-value">
                    {centreDailyIntel.daily_intelligence.expected_arrivals_today_quintals || 0} <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Quintals</span>
                  </div>
                  <span style={{ fontSize: '0.7rem', color: '#0284c7', fontWeight: 600 }}>[Model Forecast]</span>
                </div>

                <div className="briefing-stat-card">
                  <span className="briefing-stat-label">Capacity Forecast</span>
                  <div className="briefing-stat-value">
                    {centreDailyIntel.daily_intelligence.capacity_forecast?.projected_utilization_percent || 0}%
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 600, color: (centreDailyIntel.daily_intelligence.capacity_forecast?.projected_utilization_percent || 0) > 85 ? 'var(--danger-text)' : 'var(--success-text)' }}>
                    {centreDailyIntel.daily_intelligence.capacity_forecast?.projected_procurement_quintals || 0} / {centreDailyIntel.daily_intelligence.capacity_forecast?.max_daily_capacity_quintals || 0} Q
                  </span>
                </div>

                <div className="briefing-stat-card">
                  <span className="briefing-stat-label">Storage Forecast</span>
                  <div className="briefing-stat-value">
                    {centreDailyIntel.daily_intelligence.storage_forecast?.projected_utilization_percent || 0}%
                  </div>
                  <span style={{ fontSize: '0.7rem', color: '#d97706', fontWeight: 600 }}>
                    {centreDailyIntel.daily_intelligence.storage_forecast?.current_storage_quintals?.toLocaleString() || 0} / {centreDailyIntel.daily_intelligence.storage_forecast?.total_storage_quintals?.toLocaleString() || 0} Q
                  </span>
                </div>

                <div className="briefing-stat-card">
                  <span className="briefing-stat-label">Truck Requirement</span>
                  <div className="briefing-stat-value">
                    {centreDailyIntel.daily_intelligence.truck_fleet?.required || 0} <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Trucks</span>
                  </div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 600, color: (centreDailyIntel.daily_intelligence.truck_fleet?.shortfall || 0) > 0 ? 'var(--danger-text)' : 'var(--success-text)' }}>
                    Avail: {centreDailyIntel.daily_intelligence.truck_fleet?.available || 0} • Shortfall: {centreDailyIntel.daily_intelligence.truck_fleet?.shortfall || 0}
                  </span>
                </div>
              </div>

              {/* High priority perishable crops row if present */}
              {centreDailyIntel.daily_intelligence.high_priority_crops && centreDailyIntel.daily_intelligence.high_priority_crops.length > 0 && (
                <div style={{ marginTop: '12px', padding: '10px 14px', borderRadius: '8px', background: 'var(--danger-bg)', border: '1px solid var(--danger)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertCircle size={16} color="var(--danger-text)" />
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--danger-text)' }}>
                      Perishable Priority: {centreDailyIntel.daily_intelligence.high_priority_crops.map(c => `${c.crop} (${c.perishability} Perishability, Score: ${c.priority_score})`).join(', ')}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--secondary)' }}>
                    {centreDailyIntel.daily_intelligence.high_priority_crops[0]?.action}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* HIERARCHY ITEM 1: CLOSED / NON-OPERATIONAL DATE NOTICE */}
          {isClosedDate ? (
            <div className="card shadow-sm mb-4" style={{ padding: '32px', textAlign: 'center', background: 'var(--danger-bg)', border: '1.5px solid var(--danger)', borderRadius: '14px' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: 'var(--danger-bg)', color: 'var(--danger)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 12px auto' }}>
                <CalendarOff size={32} />
              </div>
              <h2 style={{ fontSize: '1.6rem', color: 'var(--danger-text)', fontWeight: 800, marginBottom: '8px' }}>
                Centre Closed — {formatDateDisplay(selectedDate)}
              </h2>
              <p style={{ fontSize: '1rem', color: 'var(--danger-text)', fontWeight: 600, margin: 0 }}>
                Reason: {closedReasonText}
              </p>
              <p style={{ fontSize: '0.875rem', color: 'var(--muted)', marginTop: '8px' }}>
                No crop procurement or appointment slots are scheduled for this date.
              </p>
            </div>
          ) : slots.length === 0 ? (
            /* HIERARCHY ITEM 1 ALT: NO SCHEDULE CONFIGURED FOR DATE */
            <div className="card shadow-sm mb-4" style={{ padding: '32px', textAlign: 'center', background: 'var(--bg-card)', border: '1px dashed var(--border)', borderRadius: '14px' }}>
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
                  border: '1px solid var(--border)',
                  background: 'var(--bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      DAILY QUINTAL CAPACITY
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'var(--info-bg)', color: 'var(--info-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Scale size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--secondary)', lineHeight: 1.2 }}>
                      {dailyCapacityInfo.max_quintals_per_day || 0} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--muted)' }}>Quintals</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '4px' }}>
                      Max daily limit for {formatDateDisplay(selectedDate)}
                    </div>
                  </div>
                </div>

                {/* Card 2: Booked Quantity */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      BOOKED
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'var(--success-bg)', color: 'var(--success-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Wheat size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--primary)', lineHeight: 1.2 }}>
                      {dailyCapacityInfo.booked_quintals || 0} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--primary-hover)' }}>Quintals</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '4px' }}>
                      Booked total for {formatDateDisplay(selectedDate)}
                    </div>
                  </div>
                </div>

                {/* Card 3: Remaining Capacity */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      REMAINING
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'var(--warning-bg)', color: 'var(--warning-text)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Clock size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--warning-text)', lineHeight: 1.2 }}>
                      {Math.max(0, (dailyCapacityInfo.max_quintals_per_day || 0) - (dailyCapacityInfo.booked_quintals || 0))} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--muted)' }}>Quintals</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '4px' }}>
                      Remaining = Max ({dailyCapacityInfo.max_quintals_per_day || 0}) − Booked ({dailyCapacityInfo.booked_quintals || 0})
                    </div>
                  </div>
                </div>

                {/* Card 4: Total Appointments */}
                <div className="card shadow-sm" style={{
                  padding: '20px',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  background: 'var(--bg-card)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                      Total Appointments
                    </span>
                    <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(124, 58, 237, 0.15)', color: '#a78bfa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Users size={20} />
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--secondary)', lineHeight: 1.2 }}>
                      {totalBookingsCount} <span style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--muted)' }}>Farmers</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: '4px' }}>
                      {remainingCapacitySelectedDate} slot capacity available
                    </div>
                  </div>
                </div>
              </div>

              {/* CENTRE OPERATIONAL INTELLIGENCE / PREDICTIVE AI (Prompt 2 - Section 1) */}
              {opIntelligence && (
                <div className="card shadow-sm mb-4" style={{ padding: '24px', borderTop: '4px solid #6366f1', background: 'var(--bg-card)', borderRadius: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Brain size={22} color="#6366f1" />
                      <div>
                        <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary)', margin: 0 }}>
                          Centre Operational Intelligence & Forecasting
                        </h3>
                        <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                          Real-time yard throughput, congestion surveillance, and fleet requirements
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span className="badge badge-confirmed" style={{ fontSize: '0.72rem', fontWeight: 700 }}>
                        CONFIRMED DATA: ACTUAL
                      </span>
                      <span className="badge badge-warning" style={{ fontSize: '0.72rem', fontWeight: 700 }}>
                        MODEL FORECAST: PREDICTED
                      </span>
                      <span className="badge" style={{ backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontSize: '0.72rem', fontWeight: 700 }}>
                        FLEET / INVENTORY: ESTIMATED
                      </span>
                    </div>
                  </div>

                  {/* Operational Intelligence Cards Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                    {/* Card 1: Expected Arrivals & Procurement */}
                    <div style={{ background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                          7-Day Arrivals & Procurement
                        </span>
                        <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                          {opIntelligence.expected_arrivals?.label || 'Predicted'}
                        </span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '6px' }}>
                        <div>
                          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'block' }}>Expected Arrivals</span>
                          <strong style={{ fontSize: '1.25rem', color: 'var(--secondary)' }}>
                            {opIntelligence.expected_arrivals?.value || 0} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>Q</span>
                          </strong>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>[Predicted]</span>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'block' }}>Expected Procurement</span>
                          <strong style={{ fontSize: '1.25rem', color: 'var(--primary)' }}>
                            {opIntelligence.expected_procurement?.value || 0} <span style={{ fontSize: '0.75rem', fontWeight: 500 }}>Q</span>
                          </strong>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>[Predicted]</span>
                        </div>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '8px' }}>
                        {opIntelligence.expected_arrivals?.basis}
                      </div>
                    </div>

                    {/* Card 2: Yard Utilization Forecast */}
                    <div style={{ background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                          Storage Utilization
                        </span>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <span className="badge badge-confirmed" style={{ fontSize: '0.65rem' }}>
                            Actual
                          </span>
                          <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                            Predicted
                          </span>
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '6px' }}>
                        <div>
                          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'block' }}>Current Utilization</span>
                          <strong style={{ fontSize: '1.25rem', color: 'var(--secondary)' }}>
                            {opIntelligence.utilization_forecast?.current_utilization_percent || 0}%
                          </strong>
                          <span style={{ fontSize: '0.68rem', color: 'var(--primary)', fontWeight: 700, display: 'block' }}>[Actual]</span>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'block' }}>Predicted Utilization</span>
                          <strong style={{ fontSize: '1.25rem', color: '#6366f1' }}>
                            {opIntelligence.utilization_forecast?.predicted_utilization_percent || 0}%
                          </strong>
                          <span style={{ fontSize: '0.68rem', color: '#d97706', fontWeight: 700, display: 'block' }}>[Predicted]</span>
                        </div>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '8px' }}>
                        Current: {opIntelligence.utilization_forecast?.current_storage_quintals?.toLocaleString()} Q / Total: {opIntelligence.utilization_forecast?.total_storage_quintals?.toLocaleString()} Q
                      </div>
                    </div>

                    {/* Card 3: Yard Congestion Level */}
                    <div style={{ background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                          Yard Congestion Status
                        </span>
                        <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                          Predicted
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '6px' }}>
                        <div style={{
                          padding: '6px 14px',
                          borderRadius: '8px',
                          fontWeight: 800,
                          fontSize: '1.1rem',
                          backgroundColor: opIntelligence.congestion_prediction?.level === 'CRITICAL' ? 'var(--danger-bg)' : opIntelligence.congestion_prediction?.level === 'HIGH' ? 'var(--warning-bg)' : opIntelligence.congestion_prediction?.level === 'MEDIUM' ? 'var(--warning-bg)' : 'var(--success-bg)',
                          color: opIntelligence.congestion_prediction?.level === 'CRITICAL' ? 'var(--danger-text)' : opIntelligence.congestion_prediction?.level === 'HIGH' ? 'var(--warning-text)' : opIntelligence.congestion_prediction?.level === 'MEDIUM' ? 'var(--warning-text)' : 'var(--success-text)'
                        }}>
                          {opIntelligence.congestion_prediction?.level || 'LOW'}
                        </div>
                        <span style={{ fontSize: '0.72rem', color: 'var(--muted)' }}>
                          Load: {opIntelligence.congestion_prediction?.load_ratio_percent || 0}%
                        </span>
                      </div>
                      <p style={{ fontSize: '0.75rem', color: 'var(--muted)', margin: '8px 0 0 0', lineHeight: 1.35 }}>
                        {opIntelligence.congestion_prediction?.description}
                      </p>
                    </div>

                    {/* Card 4: Truck Fleet Requirement */}
                    <div style={{ background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                          Truck Requirement
                        </span>
                        <span className="badge" style={{ backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontSize: '0.65rem' }}>
                          Estimated
                        </span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', textAlign: 'center', marginTop: '6px' }}>
                        <div style={{ background: 'var(--bg-card)', padding: '6px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Required</span>
                          <strong style={{ fontSize: '1.1rem', color: 'var(--secondary)' }}>{opIntelligence.truck_requirement?.estimated_required || 0}</strong>
                          <span style={{ fontSize: '0.62rem', color: 'var(--muted)', display: 'block' }}>[Estimated]</span>
                        </div>
                        <div style={{ background: 'var(--bg-card)', padding: '6px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Available</span>
                          <strong style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>{opIntelligence.truck_requirement?.available || 0}</strong>
                          <span style={{ fontSize: '0.62rem', color: 'var(--primary)', display: 'block' }}>[Actual]</span>
                        </div>
                        <div style={{ background: 'var(--bg-card)', padding: '6px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Shortfall</span>
                          <strong style={{ fontSize: '1.1rem', color: (opIntelligence.truck_requirement?.shortfall || 0) > 0 ? 'var(--danger)' : 'var(--primary)' }}>
                            {opIntelligence.truck_requirement?.shortfall || 0}
                          </strong>
                          <span style={{ fontSize: '0.62rem', color: 'var(--muted)', display: 'block' }}>[Estimated]</span>
                        </div>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '8px' }}>
                        {opIntelligence.truck_requirement?.basis}
                      </div>
                    </div>

                    {/* Card 5: Bardan Requirement */}
                    <div style={{ background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)', gridColumn: 'span 2' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase' }}>
                          Bardan (Jute Bag) Requirement & Stock
                        </span>
                        <span className="badge" style={{ backgroundColor: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontSize: '0.65rem' }}>
                          Estimated
                        </span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', textAlign: 'center', marginTop: '6px' }}>
                        <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Current Stock</span>
                          <strong style={{ fontSize: '1.15rem', color: 'var(--secondary)' }}>{opIntelligence.bardan_requirement?.current_stock_bags?.toLocaleString() || 0}</strong>
                          <span style={{ fontSize: '0.65rem', color: 'var(--primary)', fontWeight: 700, display: 'block' }}>[Actual]</span>
                        </div>
                        <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Exp. Consumption</span>
                          <strong style={{ fontSize: '1.15rem', color: 'var(--info)' }}>{opIntelligence.bardan_requirement?.expected_consumption_bags?.toLocaleString() || 0}</strong>
                          <span style={{ fontSize: '0.65rem', color: 'var(--muted)', display: 'block' }}>[Estimated]</span>
                        </div>
                        <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Projected Need</span>
                          <strong style={{ fontSize: '1.15rem', color: '#818cf8' }}>{opIntelligence.bardan_requirement?.projected_requirement_bags?.toLocaleString() || 0}</strong>
                          <span style={{ fontSize: '0.65rem', color: 'var(--muted)', display: 'block' }}>[Estimated]</span>
                        </div>
                        <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.68rem', color: 'var(--muted)', display: 'block' }}>Potential Shortage</span>
                          <strong style={{ fontSize: '1.15rem', color: (opIntelligence.bardan_requirement?.potential_shortage_bags || 0) > 0 ? 'var(--danger)' : 'var(--primary)' }}>
                            {opIntelligence.bardan_requirement?.potential_shortage_bags || 0}
                          </strong>
                          <span style={{ fontSize: '0.65rem', color: 'var(--muted)', display: 'block' }}>[Estimated]</span>
                        </div>
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--muted)', marginTop: '8px' }}>
                        {opIntelligence.bardan_requirement?.basis}
                      </div>
                    </div>

                    {/* Card 6: Capacity Saturation & Exhaustion Date (Requirement 4) */}
                    <div style={{ background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)', gridColumn: 'span 2' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Clock size={14} color="#f59e0b" /> Capacity Saturation & Early Warning Timeline
                        </span>
                        <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                          Predictive Model
                        </span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', marginTop: '6px' }}>
                        <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'block' }}>Days Until 100% Saturation</span>
                          <strong style={{ fontSize: '1.3rem', color: (opIntelligence.capacity_saturation?.days_until_full || 5) <= 3 ? '#ef4444' : '#f59e0b' }}>
                            {opIntelligence.capacity_saturation?.days_until_full ?? 4} Days
                          </strong>
                          <span style={{ fontSize: '0.7rem', color: 'var(--muted)', display: 'block', marginTop: '2px' }}>
                            Projected Saturation Date: <strong>{opIntelligence.capacity_saturation?.saturation_date || 'Within 4-5 days'}</strong>
                          </span>
                        </div>
                        <div style={{ background: 'var(--bg-card)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--muted)', display: 'block' }}>Early Warning Status</span>
                          <span style={{
                            display: 'inline-block',
                            marginTop: '4px',
                            padding: '4px 10px',
                            borderRadius: '6px',
                            fontWeight: 700,
                            fontSize: '0.85rem',
                            background: (opIntelligence.capacity_saturation?.status === 'CRITICAL' || opIntelligence.congestion_prediction?.level === 'CRITICAL') ? 'var(--danger-bg)' : 'var(--warning-bg)',
                            color: (opIntelligence.capacity_saturation?.status === 'CRITICAL' || opIntelligence.congestion_prediction?.level === 'CRITICAL') ? 'var(--danger-text)' : 'var(--warning-text)'
                          }}>
                            {opIntelligence.capacity_saturation?.status || 'MONITORING'} — {opIntelligence.congestion_prediction?.level || 'MODERATE'} Congestion
                          </span>
                          <p style={{ fontSize: '0.75rem', color: 'var(--muted)', margin: '6px 0 0 0' }}>
                            {opIntelligence.capacity_saturation?.recommendation || 'Automated early warning will trigger proactive farmer redirection before yard lockout.'}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Card 7: Automated Centre Redirection Recommendations (Requirement 5) */}
                    {redirectionOptions?.alternative_centres && redirectionOptions.alternative_centres.length > 0 && (
                      <div style={{
                        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.7))',
                        padding: '16px',
                        borderRadius: '10px',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        gridColumn: 'span 2'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Route size={18} color="#60a5fa" />
                            <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#93c5fd', textTransform: 'uppercase' }}>
                              Automated Centre Redirection Intelligence
                            </span>
                          </div>
                          <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                            Trigger: {redirectionOptions.reason || 'Yard congestion & capacity saturation risk'}
                          </span>
                        </div>
                        <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0 0 10px 0' }}>
                          When centre capacity nears saturation or enters HIGH/CRITICAL congestion, the system identifies suitable alternate centres based on distance, available intake capacity, crop support, and slot availability:
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                          {redirectionOptions.alternative_centres.map((alt, idx) => (
                            <div key={idx} style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <strong style={{ fontSize: '0.9rem', color: '#f8fafc' }}>{alt.name}</strong>
                                <span style={{ fontSize: '0.72rem', background: 'rgba(59, 130, 246, 0.2)', color: '#93c5fd', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                                  {alt.distance_km} km away
                                </span>
                              </div>
                              <div style={{ display: 'flex', gap: '8px', fontSize: '0.75rem', color: '#cbd5e1', marginTop: '6px' }}>
                                <span>Avail Cap: <strong style={{ color: '#4ade80' }}>{alt.available_capacity_quintals} Q</strong></span>
                                <span>•</span>
                                <span>Congestion: <strong style={{ color: alt.predicted_congestion === 'LOW' ? '#4ade80' : '#fbbf24' }}>{alt.predicted_congestion}</strong></span>
                              </div>
                              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: '4px' }}>
                                Crops: {Array.isArray(alt.crops_supported) ? alt.crops_supported.join(', ') : alt.crops_supported}
                              </div>
                              <div style={{ fontSize: '0.72rem', color: '#60a5fa', marginTop: '6px', fontStyle: 'italic' }}>
                                {alt.recommended_action}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}


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
                  <div style={{ textAlign: 'center', padding: '24px', background: 'var(--bg-page)', borderRadius: '8px', border: '1px dashed var(--border)' }}>
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
                        <tr style={{ background: 'var(--bg-page)' }}>
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
                        <tr style={{ background: 'var(--success-bg)', borderTop: '2px solid var(--primary-border)' }}>
                          <td style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--success-text)', padding: '14px 16px' }}>
                            Total
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 800, fontSize: '1.05rem', color: 'var(--success-text)', padding: '14px 16px' }}>
                            {totalBookingsCount} Bookings
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: 800, fontSize: '1.1rem', color: 'var(--primary)', padding: '14px 16px' }}>
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
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--info-text)', background: 'var(--info-bg)', padding: '6px 12px', borderRadius: '8px' }}>
              Total: {bookings.length} Appointments
            </span>
          </div>

          {isClosedDate ? (
            <div style={{ textAlign: 'center', padding: '32px', background: 'var(--danger-bg)', borderRadius: '12px', border: '1px solid var(--danger)' }}>
              <h3 style={{ color: 'var(--danger-text)', fontWeight: 800 }}>Centre Closed on {formatDateDisplay(selectedDate)}</h3>
              <p style={{ color: 'var(--danger-text)' }}>Reason: {closedReasonText}</p>
            </div>
          ) : loading ? (
            <p style={{ padding: '16px' }}>Loading appointments for {formatDateDisplay(selectedDate)}...</p>
          ) : bookings.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px', background: 'var(--bg-page)', borderRadius: '12px', border: '1px dashed var(--border)' }}>
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
                  <div key={slot.id} style={{ border: '1px solid var(--border)', borderRadius: '12px', overflow: 'hidden' }}>
                    {/* Slot Group Header */}
                    <div style={{ background: 'var(--bg-page)', padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <Clock size={18} color="var(--primary)" />
                        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0, color: 'var(--secondary)' }}>
                          {slot.start_time} – {slot.end_time}
                        </h3>
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.875rem', color: slot.is_full ? 'var(--danger)' : 'var(--primary)' }}>
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
                                    <span style={{ color: 'var(--success)', fontWeight: 800, fontSize: '0.85rem', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                      VERIFIED <CheckCircle size={14} />
                                    </span>
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
                                        style={{ backgroundColor: 'var(--info-bg)', color: 'var(--info-text)', borderColor: 'var(--info)' }}
                                        onClick={() => handleStatusChange(b.appointment_id || b.booking_id, 'ARRIVED')}
                                        disabled={updatingStatusId === (b.appointment_id || b.booking_id)}
                                        title="Mark Farmer Arrived"
                                      >
                                        <UserCheck size={14} /> Arrived
                                      </button>
                                    )}

                                    {['ARRIVED', 'VERIFIED', 'RECEIVED', 'QUALITY_CHECKED', 'WEIGHED', 'STORED', 'PAYMENT_INITIATED'].includes(b.status) && (
                                      <button 
                                        className="btn btn-primary btn-sm"
                                        onClick={() => {
                                          if (navigate) {
                                            navigate('centre-process', { appointmentId: b.appointment_id || b.booking_id });
                                          } else {
                                            handleOpenProcurementModal(b);
                                          }
                                        }}
                                        title="Open Dedicated 5-Step Procurement & AI Quality Workflow"
                                      >
                                        <Scale size={14} /> Process ({b.status})
                                      </button>
                                    )}

                                    {(['COMPLETED', 'PROCURED', 'PAID'].includes(b.status) || b.is_all_completed) && (
                                      <button 
                                        className="btn btn-sm"
                                        style={{ background: '#2563eb', color: '#fff', borderColor: '#1d4ed8', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                                        onClick={() => {
                                          if (navigate) {
                                            navigate('centre-storage', { appointmentId: b.appointment_id || b.booking_id });
                                          }
                                        }}
                                        title="Open Dedicated Storage Page & Final Warehouse Verification"
                                      >
                                        <Warehouse size={14} /> Storage
                                      </button>
                                    )}

                                    {b.status !== 'REJECTED' && b.status !== 'PAID' && (
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
            background: 'var(--success-bg)',
            border: '1px solid var(--primary-border)',
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
              <div style={{ fontSize: '0.85rem', color: 'var(--success-text)', fontWeight: 700, textTransform: 'uppercase' }}>
                Daily Quintal Capacity for {formatDateDisplay(selectedDate)}
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--success-text)', marginTop: '4px' }}>
                {dailyCapacityInfo.booked_quintals} / {dailyCapacityInfo.max_quintals_per_day} Quintals Booked
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--primary)', marginTop: '2px' }}>
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
        <>
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
                  <label key={day} style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer', padding: '8px 12px', borderRadius: '8px', background: isChecked ? 'var(--success-bg)' : 'var(--bg-page)', border: `1px solid ${isChecked ? 'var(--primary-border)' : 'var(--border)'}` }}>
                    <input 
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggleOperatingDay(day)}
                      style={{ width: '18px', height: '18px', accentColor: 'var(--primary)' }}
                    />
                    <span style={{ fontWeight: 600, color: isChecked ? 'var(--success-text)' : 'var(--text-secondary)' }}>{day}</span>
                    {isChecked ? (
                      <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 700, color: 'var(--success)', textTransform: 'uppercase' }}>Open</span>
                    ) : (
                      <span style={{ marginLeft: 'auto', fontSize: '0.75rem', fontWeight: 700, color: 'var(--danger)', textTransform: 'uppercase' }}>Closed</span>
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
            <form onSubmit={handleAddNonOpDate} style={{ marginBottom: '20px', background: 'var(--bg-page)', padding: '16px', borderRadius: '10px', border: '1px solid var(--border)' }}>
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
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', textAlign: 'center', padding: '16px', background: 'var(--bg-page)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                No holiday exceptions configured.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '320px', overflowY: 'auto' }}>
                {nonOperationalDates.map(item => (
                  <div key={item.date} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'var(--danger-bg)', borderRadius: '8px', border: '1px solid var(--danger)' }}>
                    <div>
                      <div style={{ fontWeight: 700, color: 'var(--danger-text)', fontSize: '0.9rem' }}>{formatDateDisplay(item.date)}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--danger-text)' }}>{item.reason}</div>
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

        {/* Section 3: Centre Staff & Operating Employee Roster (Requirement 2) */}
        <div className="card shadow-sm" style={{ padding: '24px', marginTop: '20px', borderRadius: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px' }}>
            <div>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--secondary)' }}>
                <Users size={20} color="var(--primary)" /> Centre Staff & Operating Employee Roster
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                Authorized officers and operators registered in database for gate intake, QC, AI inspection, weighment, and storage checks.
              </p>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, background: 'var(--primary-light)', color: 'var(--primary)', padding: '4px 12px', borderRadius: '20px' }}>
              {employees.length} Active Employees
            </span>
          </div>

          {empError && (
            <div className="alert alert-danger" style={{ marginBottom: '16px', padding: '10px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertTriangle size={15} /> {empError}
            </div>
          )}

          {empSuccess && (
            <div className="alert alert-success" style={{ marginBottom: '16px', padding: '10px 14px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={15} /> {empSuccess}
            </div>
          )}

          {/* Existing Employees Table */}
          {loadingEmployees ? (
            <p style={{ padding: '16px', color: 'var(--muted)' }}>Loading centre staff roster...</p>
          ) : employees.length === 0 ? (
            <p style={{ padding: '16px', color: 'var(--muted)', fontStyle: 'italic' }}>No staff members registered. Add new employees below.</p>
          ) : (
            <div className="table-container" style={{ marginBottom: '24px' }}>
              <table className="data-table" style={{ margin: 0 }}>
                <thead>
                  <tr>
                    <th>Employee Name</th>
                    <th>Role / Assignment</th>
                    <th>Employee Code</th>
                    <th>Contact Phone</th>
                    <th>Email Address</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'center' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map(emp => (
                    <tr key={emp.id}>
                      <td><strong>{emp.name}</strong></td>
                      <td>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          background: emp.role?.includes('Storage') ? 'rgba(37, 99, 235, 0.1)' : emp.role?.includes('QC') ? 'rgba(16, 185, 129, 0.1)' : 'rgba(124, 58, 237, 0.1)',
                          color: emp.role?.includes('Storage') ? '#2563eb' : emp.role?.includes('QC') ? '#059669' : '#7c3aed'
                        }}>
                          {emp.role}
                        </span>
                      </td>
                      <td><code>{emp.employee_code}</code></td>
                      <td>{emp.phone || '—'}</td>
                      <td>{emp.email || '—'}</td>
                      <td>
                        <span className="badge badge-confirmed" style={{ fontSize: '0.72rem' }}>
                          {emp.status}
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          className="btn btn-outline btn-sm"
                          style={{ color: 'var(--danger)', borderColor: 'var(--danger)', padding: '2px 8px', fontSize: '0.75rem' }}
                          onClick={() => handleDeleteEmployee(emp.id, emp.name)}
                          title="Deactivate employee from centre"
                        >
                          Deactivate
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Add Employee Form */}
          <div style={{ background: 'var(--bg-page)', padding: '18px 20px', borderRadius: '10px', border: '1px solid var(--border)' }}>
            <h4 style={{ margin: '0 0 14px 0', fontSize: '0.95rem', fontWeight: 800, color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <UserPlus size={16} color="var(--primary)" /> Add New Employee to Centre Roster
            </h4>
            <form onSubmit={handleAddEmployee}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Full Name *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    placeholder="e.g. Officer Mahesh Sawant"
                    value={newEmpForm.name}
                    onChange={e => setNewEmpForm({ ...newEmpForm, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Role / Designation *</label>
                  <select
                    className="form-control"
                    value={newEmpForm.role}
                    onChange={e => setNewEmpForm({ ...newEmpForm, role: e.target.value })}
                  >
                    <option value="Intake Officer">Intake Officer (Step 1 Verification)</option>
                    <option value="Quality Inspector">Quality Inspector (Step 2 QC)</option>
                    <option value="AI QC Lead">AI QC Lead (Step 3 Vision Analysis)</option>
                    <option value="Weighbridge Operator">Weighbridge Operator (Step 4 Scale)</option>
                    <option value="Procurement Manager">Procurement Manager (Step 5 Clearance)</option>
                    <option value="Storage Supervisor">Storage Supervisor (Storage Check)</option>
                  </select>
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Employee Code</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. EMP-07"
                    value={newEmpForm.employee_code}
                    onChange={e => setNewEmpForm({ ...newEmpForm, employee_code: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Phone Contact</label>
                  <input
                    type="tel"
                    className="form-control"
                    placeholder="e.g. 9876543210"
                    value={newEmpForm.phone}
                    onChange={e => setNewEmpForm({ ...newEmpForm, phone: e.target.value })}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>Email Address</label>
                  <input
                    type="email"
                    className="form-control"
                    placeholder="e.g. officer@bharatagri.gov.in"
                    value={newEmpForm.email}
                    onChange={e => setNewEmpForm({ ...newEmpForm, email: e.target.value })}
                  />
                </div>
              </div>
              <button
                type="submit"
                className="btn btn-primary btn-sm"
                disabled={addingEmp}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                <Plus size={14} /> {addingEmp ? 'Adding Employee...' : 'Add Employee to Roster'}
              </button>
            </form>
          </div>
        </div>
        </>
      )}

      {/* TAB 5: CENTRE ALERTS SECTION (Requirement 6) */}
      {activeTab === 'alerts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '2.5rem' }}>
          <div className="card shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '16px', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={22} color="#ef4444" /> Operational Alert Surveillance
                </h3>
                <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>
                  Active operational triggers, capacity warnings, fleet shortages, and anomaly reviews
                </span>
              </div>

              {/* Filter Tabs */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'RESOLVED'].map(filterKey => (
                  <button
                    key={filterKey}
                    onClick={() => setAlertFilter(filterKey)}
                    className="btn btn-sm"
                    style={{
                      background: alertFilter === filterKey ? 'var(--primary)' : 'var(--bg-page)',
                      color: alertFilter === filterKey ? '#fff' : 'var(--secondary)',
                      border: '1px solid var(--border)',
                      fontWeight: alertFilter === filterKey ? 700 : 500
                    }}
                  >
                    {filterKey}
                  </button>
                ))}
              </div>
            </div>

            {/* Alert List */}
            {centreAlerts.filter(a => {
              if (alertFilter === 'ALL') return true;
              if (alertFilter === 'RESOLVED') return a.status === 'RESOLVED';
              return a.severity === alertFilter;
            }).length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px 20px', background: 'var(--bg-page)', borderRadius: '10px', border: '1px dashed var(--border)' }}>
                <Check size={36} color="var(--primary)" style={{ margin: '0 auto 8px auto' }} />
                <h4 style={{ margin: 0, color: 'var(--secondary)' }}>No Alerts Found</h4>
                <p style={{ margin: '6px 0 0 0', fontSize: '0.85rem', color: 'var(--muted)' }}>
                  No operational alerts matching filter criteria "{alertFilter}" for this centre.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {centreAlerts.filter(a => {
                  if (alertFilter === 'ALL') return true;
                  if (alertFilter === 'RESOLVED') return a.status === 'RESOLVED';
                  return a.severity === alertFilter;
                }).map(alert => (
                  <div key={alert.id} style={{
                    padding: '18px 20px',
                    borderRadius: '10px',
                    background: alert.severity === 'CRITICAL' ? 'rgba(239, 68, 68, 0.04)' : alert.severity === 'HIGH' ? 'rgba(245, 158, 11, 0.04)' : 'var(--bg-page)',
                    borderLeft: `5px solid ${alert.severity === 'CRITICAL' ? '#ef4444' : alert.severity === 'HIGH' ? '#f59e0b' : '#3b82f6'}`,
                    border: '1px solid var(--border)',
                    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.02)'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.72rem',
                          fontWeight: 800,
                          textTransform: 'uppercase',
                          background: alert.severity === 'CRITICAL' ? 'var(--danger-bg)' : alert.severity === 'HIGH' ? 'var(--warning-bg)' : 'var(--info-bg)',
                          color: alert.severity === 'CRITICAL' ? 'var(--danger-text)' : alert.severity === 'HIGH' ? 'var(--warning-text)' : 'var(--info-text)'
                        }}>
                          {alert.severity}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                          Alert #{alert.id} • {alert.alert_type}
                        </span>
                        {alert.status === 'RESOLVED' && (
                          <span className="badge badge-confirmed" style={{ fontSize: '0.7rem' }}>RESOLVED</span>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '0.78rem', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Clock size={12} /> {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Recent'}
                        </span>
                        {alert.status !== 'RESOLVED' && (
                          <button
                            onClick={() => handleResolveAlert(alert.id)}
                            disabled={resolvingAlertId === alert.id}
                            className="btn btn-primary btn-sm"
                            style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                          >
                            {resolvingAlertId === alert.id ? 'Resolving...' : 'Mark Resolved'}
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Event, Location, Timestamp, Cause, Severity, Recommended Action */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid var(--border)' }}>
                      <div>
                        <strong style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--muted)', display: 'block' }}>WHAT Happened (Event)</strong>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--secondary)', marginTop: '2px' }}>
                          {alert.what_happened || alert.title || alert.what || alert.event || 'Operational Threshold Flagged'}
                        </div>
                      </div>
                      <div>
                        <strong style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--muted)', display: 'block' }}>WHERE (Location)</strong>
                        <div style={{ fontSize: '0.85rem', color: 'var(--secondary)', marginTop: '2px' }}>
                          {alert.where_location || alert.where || alert.centre_name || 'Procurement Yard'}
                        </div>
                      </div>
                      <div>
                        <strong style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--muted)', display: 'block' }}>WHEN (Timestamp)</strong>
                        <div style={{ fontSize: '0.85rem', color: 'var(--secondary)', marginTop: '2px' }}>
                          {alert.when || (alert.when_timestamp ? new Date(alert.when_timestamp).toLocaleString() : (alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Recent'))}
                        </div>
                      </div>
                      <div>
                        <strong style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--muted)', display: 'block' }}>WHY Flagged (Cause / Metric)</strong>
                        <div style={{ fontSize: '0.85rem', color: 'var(--secondary)', marginTop: '2px' }}>
                          {alert.why_flagged || alert.why_reason || alert.why || alert.cause || alert.description || 'Threshold metric variance detected'}
                        </div>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <strong style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--primary)', display: 'block' }}>RECOMMENDED ACTION</strong>
                        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary-dark)', marginTop: '2px', background: 'var(--success-bg)', padding: '6px 10px', borderRadius: '6px' }}>
                          {alert.recommended_action || alert.action || 'Review queue status and adjust appointment schedules.'}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 6: CENTRE INSIGHTS ENGINE (Requirement 8) */}
      {activeTab === 'insights' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '2.5rem' }}>
          <div className="card shadow-sm" style={{ padding: '24px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '16px', marginBottom: '20px' }}>
              <div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--secondary)', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Brain size={24} color="#6366f1" /> Centre Operational Insights Engine
                </h3>
                <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                  Grounded in actual database records and XGBoost forecasting — not generic AI text
                </span>
              </div>
              <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#6366f1', fontWeight: 700 }}>
                DESCRIPTIVE • PREDICTIVE • PRESCRIPTIVE
              </span>
            </div>

            {/* 3 Columns of Grounded Insights */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
              {/* Column 1: Descriptive - What is happening */}
              <div style={{ background: 'var(--bg-page)', padding: '18px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '2px solid #3b82f6', paddingBottom: '8px' }}>
                  <Activity size={18} color="#3b82f6" />
                  <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Descriptive: What Is Happening
                  </h4>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {(centreInsights?.descriptive || [
                    `Current appointment volume: ${bookings.length} farmers scheduled for ${formatDateDisplay(selectedDate)}.`,
                    `Current booked quintals: ${dailyCapacityInfo.booked_quintals || 0} Q against ${dailyCapacityInfo.max_quintals_per_day || 500} Q daily intake limit.`,
                    `Active crop varieties currently being processed: ${cropSummaryList.length} crops recorded in yard.`,
                    `Storage capacity currently holding: ${opIntelligence?.utilization_forecast?.current_storage_quintals?.toLocaleString() || '1,200'} Quintals.`
                  ]).map((item, idx) => {
                    const isExpanded = !!expandedInsights[`desc_${idx}`];
                    const title = typeof item === 'string' ? item : (item.what || item.summary || item.text);
                    return (
                      <div key={idx} style={{ background: 'var(--bg-card)', borderRadius: '8px', border: isExpanded ? '1px solid #3b82f6' : '1px solid var(--border)', overflow: 'hidden' }}>
                        <div
                          onClick={() => toggleInsight(`desc_${idx}`)}
                          style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', gap: '8px', background: isExpanded ? 'rgba(59, 130, 246, 0.04)' : 'transparent' }}
                        >
                          <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--secondary)' }}>{title}</div>
                          <span style={{ color: 'var(--muted)', display: 'flex' }}>{isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</span>
                        </div>
                        {isExpanded && typeof item === 'object' && (
                          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {item.evidence && <div><strong style={{ color: 'var(--muted)' }}>Supporting Data / Evidence:</strong> <span style={{ color: 'var(--secondary)' }}>{item.evidence}</span></div>}
                            {item.why && <div><strong style={{ color: 'var(--muted)' }}>Explanation:</strong> <span style={{ color: 'var(--secondary)' }}>{item.why}</span></div>}
                            {item.action && <div style={{ background: 'var(--success-bg)', padding: '4px 8px', borderRadius: '4px' }}><strong style={{ color: 'var(--primary-dark)' }}>Recommended Action:</strong> <span style={{ color: 'var(--primary-dark)' }}>{item.action}</span></div>}
                            {item.benefit && <div><strong style={{ color: 'var(--muted)' }}>Expected Benefit:</strong> <span style={{ color: 'var(--muted)' }}>{item.benefit}</span></div>}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Column 2: Predictive - What may happen */}
              <div style={{ background: 'var(--bg-page)', padding: '18px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '2px solid #f59e0b', paddingBottom: '8px' }}>
                  <Clock size={18} color="#f59e0b" />
                  <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Predictive: What May Happen
                  </h4>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {(centreInsights?.predictive || [
                    `Yard capacity is projected to reach saturation in ${opIntelligence?.capacity_saturation?.days_until_full || 4} days (${opIntelligence?.capacity_saturation?.saturation_date || 'Projected'}).`,
                    `Expected procurement over next 7 days estimated at ${opIntelligence?.expected_procurement?.value || 450} Quintals.`,
                    `Predicted yard congestion level is ${opIntelligence?.congestion_prediction?.level || 'LOW'} with load ratio of ${opIntelligence?.congestion_prediction?.load_ratio_percent || 45}%.`,
                    `Truck fleet deficit predicted: ${opIntelligence?.truck_requirement?.shortfall || 0} additional trucks needed for outgoing transit.`
                  ]).map((item, idx) => {
                    const isExpanded = !!expandedInsights[`pred_${idx}`];
                    const title = typeof item === 'string' ? item : (item.what || item.summary || item.text);
                    return (
                      <div key={idx} style={{ background: 'var(--bg-card)', borderRadius: '8px', border: isExpanded ? '1px solid #f59e0b' : '1px solid var(--border)', overflow: 'hidden' }}>
                        <div
                          onClick={() => toggleInsight(`pred_${idx}`)}
                          style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', gap: '8px', background: isExpanded ? 'rgba(245, 158, 11, 0.04)' : 'transparent' }}
                        >
                          <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--secondary)' }}>{title}</div>
                          <span style={{ color: 'var(--muted)', display: 'flex' }}>{isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</span>
                        </div>
                        {isExpanded && typeof item === 'object' && (
                          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {item.evidence && <div><strong style={{ color: 'var(--muted)' }}>Supporting Data / Evidence:</strong> <span style={{ color: 'var(--secondary)' }}>{item.evidence}</span></div>}
                            {item.why && <div><strong style={{ color: 'var(--muted)' }}>Explanation:</strong> <span style={{ color: 'var(--secondary)' }}>{item.why}</span></div>}
                            {item.action && <div style={{ background: 'var(--success-bg)', padding: '4px 8px', borderRadius: '4px' }}><strong style={{ color: 'var(--primary-dark)' }}>Recommended Action:</strong> <span style={{ color: 'var(--primary-dark)' }}>{item.action}</span></div>}
                            {item.benefit && <div><strong style={{ color: 'var(--muted)' }}>Expected Benefit:</strong> <span style={{ color: 'var(--muted)' }}>{item.benefit}</span></div>}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Column 3: Prescriptive - What should be considered */}
              <div style={{ background: 'var(--bg-page)', padding: '18px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', borderBottom: '2px solid #10b981', paddingBottom: '8px' }}>
                  <Check size={18} color="#10b981" />
                  <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'var(--secondary)' }}>
                    Prescriptive: What to Consider
                  </h4>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {(centreInsights?.prescriptive || [
                    'Increase daily intake capacity or open Sunday shift if booked quintals exceed 85%.',
                    'Redistribute heavy afternoon appointments to early morning 09:00 AM slots to relieve congestion.',
                    'Prioritize dispatch of perishable crops (Tomatoes, Vegetables) within 24 hours of weighing.',
                    'Request 2 additional transit trucks from district logistics pool to avoid storage blockage.',
                    'Pre-position 400 additional Bardan (jute bags) in bay 3 before weekend arrivals surge.'
                  ]).map((item, idx) => {
                    const isExpanded = !!expandedInsights[`pres_${idx}`];
                    const title = typeof item === 'string' ? item : (item.what || item.summary || item.text);
                    return (
                      <div key={idx} style={{ background: 'var(--bg-card)', borderRadius: '8px', border: isExpanded ? '1px solid #10b981' : '1px solid var(--border)', overflow: 'hidden' }}>
                        <div
                          onClick={() => toggleInsight(`pres_${idx}`)}
                          style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', gap: '8px', background: isExpanded ? 'rgba(16, 185, 129, 0.04)' : 'transparent' }}
                        >
                          <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--secondary)' }}>{title}</div>
                          <span style={{ color: 'var(--muted)', display: 'flex' }}>{isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</span>
                        </div>
                        {isExpanded && typeof item === 'object' && (
                          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {item.evidence && <div><strong style={{ color: 'var(--muted)' }}>Supporting Data / Evidence:</strong> <span style={{ color: 'var(--secondary)' }}>{item.evidence}</span></div>}
                            {item.why && <div><strong style={{ color: 'var(--muted)' }}>Explanation:</strong> <span style={{ color: 'var(--secondary)' }}>{item.why}</span></div>}
                            {item.action && <div style={{ background: 'var(--success-bg)', padding: '4px 8px', borderRadius: '4px' }}><strong style={{ color: 'var(--primary-dark)' }}>Recommended Action:</strong> <span style={{ color: 'var(--primary-dark)' }}>{item.action}</span></div>}
                            {item.benefit && <div><strong style={{ color: 'var(--muted)' }}>Expected Benefit:</strong> <span style={{ color: 'var(--muted)' }}>{item.benefit}</span></div>}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 7: ISOLATED CENTRE COPILOT (Requirement 38) */}
      {activeTab === 'copilot' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card shadow-sm" style={{
            padding: '24px',
            borderRadius: '14px',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid var(--border)', paddingBottom: '16px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, var(--primary) 0%, #15803d 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffffff'
                }}>
                  <Bot size={24} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                    Centre Copilot — Mandi AI Sahayak
                  </h3>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    Facility: <strong style={{ color: 'var(--primary)' }}>{resolvedCentreId || centreId}</strong> ({user?.name || user?.centre_name || 'Procurement Centre'})
                  </span>
                </div>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 14px',
                borderRadius: '20px',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#10b981',
                fontSize: '0.8rem',
                fontWeight: 700
              }}>
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#10b981' }}></span>
                Strict Centre Isolation Active
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem', lineHeight: 1.5 }}>
              Ask questions about your centre's live queue length, morning bottleneck causes, appointments, procurement intake, capacity limits, and equipment status. Responses are calculated directly from your centre's database records.
            </p>

            {/* Quick Suggestion Pills */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
              {[
                "Why is my queue increasing?",
                "How many farmers are currently waiting?",
                "How many appointments do I have today?",
                "How much have we procured today?",
                "How much capacity remains for today?",
                "Which equipment is causing a delay?",
                "How many farmers are coming in the next hour?",
                "What is my current processing rate?"
              ].map((chip, cIdx) => (
                <button
                  key={cIdx}
                  type="button"
                  onClick={() => { setCentreCopilotQuery(chip); handleAskCentreCopilot(chip); }}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '20px',
                    border: '1px solid var(--border)',
                    backgroundColor: 'var(--surface-secondary)',
                    color: 'var(--text-primary)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.color = 'var(--primary)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                >
                  <MessageSquare size={13} /> {chip}
                </button>
              ))}
            </div>

            {/* Query Input */}
            <div style={{ display: 'flex', gap: '10px', marginBottom: '1.5rem' }}>
              <input
                type="text"
                placeholder="Ask about your centre's queue, intake, appointments or weighbridges..."
                value={centreCopilotQuery}
                onChange={(e) => setCentreCopilotQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleAskCentreCopilot(); }}
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--border)',
                  backgroundColor: 'var(--input-bg)',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem'
                }}
              />
              <button
                className="btn btn-primary"
                onClick={() => handleAskCentreCopilot()}
                disabled={centreCopilotLoading}
                style={{ padding: '12px 24px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '8px' }}
              >
                {centreCopilotLoading ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" /> Retrieving...
                  </>
                ) : (
                  <>
                    <Sparkles size={16} /> Ask Copilot
                  </>
                )}
              </button>
            </div>

            {/* Copilot Loading State */}
            {centreCopilotLoading && (
              <div style={{
                marginTop: '16px', padding: '16px 20px', backgroundColor: 'var(--surface)',
                borderRadius: '8px', border: '1px solid var(--border)', display: 'flex', alignItems: 'center',
                gap: '10px', color: 'var(--primary)'
              }}>
                <RefreshCw size={18} className="animate-spin" />
                <span style={{ fontSize: '0.92rem', fontWeight: 600 }}>
                  Querying centre database and verifying queue & procurement metrics...
                </span>
              </div>
            )}

            {/* Copilot Actionable Error State with Retry Button */}
            {centreCopilotError && !centreCopilotLoading && (
              <div style={{
                marginTop: '16px', padding: '16px 20px', backgroundColor: 'var(--danger-bg)',
                borderRadius: '8px', border: '1px solid var(--danger-border)', color: 'var(--danger-text)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertCircle size={20} />
                  <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{centreCopilotError}</span>
                </div>
                <button
                  onClick={() => handleAskCentreCopilot(centreCopilotLastQuery)}
                  className="btn btn-outline"
                  style={{
                    borderColor: 'currentColor', color: 'inherit',
                    padding: '6px 14px', fontSize: '0.82rem', fontWeight: 700,
                    display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer'
                  }}
                >
                  <RefreshCw size={13} /> Retry Query
                </button>
              </div>
            )}

            {/* Copilot Response Card */}
            {centreCopilotResponse && !centreCopilotLoading && (
              <ErrorBoundary title="Centre Copilot Output Error" message="Could not render Centre Copilot response safely.">
                <div style={{
                  padding: '20px',
                  borderRadius: '12px',
                  backgroundColor: 'var(--surface-secondary)',
                  border: '1px solid var(--border)',
                  borderLeft: '4px solid var(--primary)',
                  animation: 'fadeIn 0.2s ease-in-out',
                  marginTop: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', color: 'var(--primary)', fontWeight: 800, fontSize: '0.9rem' }}>
                    <Sparkles size={18} />
                    CENTRE COPILOT VERIFIED ANSWER
                  </div>

                  <p style={{ fontSize: '1rem', color: 'var(--text-primary)', lineHeight: 1.6, margin: '0 0 14px 0', fontWeight: 500 }}>
                    {centreCopilotResponse.answer || 'No records found matching your centre query criteria.'}
                  </p>

                  {/* Key Data Point Cards */}
                  {centreCopilotResponse.data_points && (
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                      gap: '12px',
                      marginTop: '14px',
                      paddingTop: '14px',
                      borderTop: '1px solid var(--border)'
                    }}>
                      {Object.entries(centreCopilotResponse.data_points).map(([key, val]) => (
                        <div key={key} style={{
                          background: 'var(--surface)',
                          padding: '10px 14px',
                          borderRadius: '8px',
                          border: '1px solid var(--border)'
                        }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, display: 'block' }}>
                            {key.replace(/_/g, ' ')}
                          </span>
                          <div style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '2px' }}>
                            {typeof val === 'number' ? (Number.isInteger(val) ? val.toLocaleString() : val.toFixed(1)) : String(val)}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Developer Query Plan & Structured Retrieval Debug Representation (Requirement 16) */}
                  {centreCopilotResponse.debug_info && (
                    <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border)' }}>
                      <button
                        onClick={() => setShowCentreCopilotDebug(!showCentreCopilotDebug)}
                        style={{
                          background: 'none', border: 'none', color: 'var(--text-secondary)',
                          fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer',
                          display: 'flex', alignItems: 'center', gap: '6px', padding: 0
                        }}
                      >
                        <Code size={14} color="var(--primary)" />
                        {showCentreCopilotDebug ? 'Hide Developer Query Plan & Retrieval Debug' : 'View Developer Query Plan & Retrieval Debug'}
                      </button>

                      {showCentreCopilotDebug && (
                        <div className="dev-debug-panel" style={{ marginTop: '10px', maxHeight: '300px', overflowY: 'auto' }}>
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', marginBottom: '8px' }}>
                            <div>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase' }}>Scope & Constraints</span>
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', marginTop: '2px' }}>
                                Centre: <strong>{centreCopilotResponse.debug_info.detected_entities?.centre || resolvedCentreId || 'C01'}</strong> | Crop: <strong>{centreCopilotResponse.debug_info.detected_entities?.crop || 'All'}</strong>
                              </div>
                            </div>
                            <div>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase' }}>Time Horizon</span>
                              <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', marginTop: '2px' }}>
                                Period: <strong>{centreCopilotResponse.debug_info.detected_time?.label || 'Today'}</strong> ({centreCopilotResponse.debug_info.detected_time?.from} to {centreCopilotResponse.debug_info.detected_time?.to})
                              </div>
                            </div>
                          </div>
                          <div>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontWeight: 700, textTransform: 'uppercase' }}>Structured Query Plan</span>
                            <pre style={{ margin: '4px 0 0 0', fontSize: '0.74rem', background: 'var(--surface)', padding: '8px', borderRadius: '4px', border: '1px solid var(--border)', color: 'var(--text-primary)', overflowX: 'auto' }}>
                              {JSON.stringify(centreCopilotResponse.debug_info, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </ErrorBoundary>
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
                <div style={{ background: 'var(--success-bg)', border: '1px solid var(--primary-border)', padding: '12px', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.85rem', color: '#166534' }}>
                  <strong>Schedule Generator Summary:</strong>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '4px' }}>
                    <CheckCircle size={13} /> Configured: <strong>{rangeSummary.created_dates_count} operating dates</strong>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '2px' }}>
                    <XCircle size={13} /> Skipped: <strong>{rangeSummary.skipped_dates_count} closed/holiday dates</strong>
                  </div>
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
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    {verificationResult.success ? (
                      <>VERIFIED <CheckCircle size={20} color="var(--success-text)" /></>
                    ) : (
                      <>{verificationResult.error || 'INVALID QR CODE'} <XCircle size={20} color="var(--danger-text)" /></>
                    )}
                  </h3>
                  <span className={`badge ${verificationResult.success ? 'badge-confirmed' : 'badge-rejected'}`}>
                    {verificationResult.success ? 'VERIFIED' : 'INVALID'}
                  </span>
                </div>

                <p style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: verificationResult.appointment ? '0.75rem' : '1rem' }}>
                  {verificationResult.message}
                </p>

                {verificationResult.appointment && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem', backgroundColor: 'var(--bg-card)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', color: 'var(--secondary)', marginBottom: '1rem' }}>
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

      {/* DETAILED PROCUREMENT PROCESSING MODAL FOR ARRIVED FARMERS */}
      {selectedArrivedBooking && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.65)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1100,
          padding: '1rem'
        }}>
          <div className="card shadow-lg" style={{
            maxWidth: '680px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '2rem',
            position: 'relative'
          }}>
            <button
              onClick={() => setSelectedArrivedBooking(null)}
              style={{
                position: 'absolute',
                top: '1.25rem',
                right: '1.25rem',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--muted)'
              }}
            >
              <X size={20} />
            </button>

            <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: '1rem', marginBottom: '1.25rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Mandi Mandated Procurement Inspection
              </span>
              <h2 style={{ fontSize: '1.4rem', color: 'var(--secondary)', marginTop: '0.2rem' }}>
                Procurement Intake: {selectedArrivedBooking.farmer_name}
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '4px 0 0 0' }}>
                Booking ID: <strong>{selectedArrivedBooking.appointment_id || selectedArrivedBooking.booking_id}</strong> • Crop: <strong>{selectedArrivedBooking.crop}</strong> • Booked: <strong>{selectedArrivedBooking.quantity} Quintals</strong>
              </p>
            </div>

            {procurementError && (
              <div style={{ padding: '0.75rem 1rem', borderRadius: 'var(--radius-sm)', marginBottom: '1rem', backgroundColor: 'var(--danger-bg)', color: 'var(--danger-text)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
                <AlertCircle size={16} />
                <span>{procurementError}</span>
              </div>
            )}

            {/* Workflow Progress Steps */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem', overflowX: 'auto', gap: '0.5rem' }}>
              {[
                ['RECEIVED', '1. Intake'],
                ['QUALITY_CHECKED', '2. Quality Check'],
                ['WEIGHED', '3. Weighment'],
                ['STORED', '4. Storage'],
                ['PAID', '5. DBT Payment']
              ].map(([st, label]) => {
                const isCurrent = (
                  (st === 'RECEIVED' && procurementStep === 'received') ||
                  (st === 'QUALITY_CHECKED' && procurementStep === 'quality') ||
                  (st === 'WEIGHED' && procurementStep === 'weighment') ||
                  (st === 'STORED' && procurementStep === 'storage') ||
                  (st === 'PAID' && (procurementStep === 'payment' || procurementStep === 'complete'))
                );
                return (
                  <div key={st} style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.35rem 0.65rem',
                    borderRadius: '9999px',
                    backgroundColor: isCurrent ? 'var(--primary)' : 'var(--bg-page)',
                    color: isCurrent ? '#ffffff' : 'var(--muted)',
                    whiteSpace: 'nowrap'
                  }}>
                    {label}
                  </div>
                );
              })}
            </div>

            {/* Form Step Inputs */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Actual Quantity Received (Quintals)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.actual_quantity}
                    onChange={(e) => {
                      const val = e.target.value;
                      const qNum = parseFloat(val) || 0;
                      const msp = procurementForm.official_msp || 2300;
                      const est = procurementForm.estimated_price || 2345;
                      setProcurementForm(f => ({
                        ...f,
                        actual_quantity: val,
                        actual_weight: val,
                        msp_reference_value: (qNum * msp).toFixed(2),
                        estimated_value: (qNum * est).toFixed(2),
                        payment_amount: (qNum * est).toFixed(2)
                      }));
                    }}
                  />
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Certified Gross Weight (Quintals)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.actual_weight}
                    onChange={(e) => setProcurementForm(f => ({ ...f, actual_weight: e.target.value }))}
                  />
                </div>
              </div>

              {/* Weighing Evidence (Section 5) */}
              {renderEvidenceSection('WEIGHING', 'Weighing Photo Evidence', 'Photo of weighbridge scale or certified tare slip.')}

              {/* Price Intelligence & Procurement Payment Breakdown */}
              <div style={{
                background: 'var(--bg-page)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
                textAlign: 'center'
              }}>
                <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    MSP Reference Value
                  </span>
                  <strong style={{ fontSize: '1.15rem', color: 'var(--secondary)', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.msp_reference_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: 'var(--muted)' }}>
                    {procurementForm.actual_quantity || 0} Q × ₹{procurementForm.official_msp || 2300}/Q MSP
                  </span>
                </div>

                <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--info-text)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    Estimated Value
                  </span>
                  <strong style={{ fontSize: '1.15rem', color: 'var(--info-text)', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.estimated_value || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: 'var(--info-text)' }}>
                    {procurementForm.actual_quantity || 0} Q × ₹{procurementForm.estimated_price || 2345}/Q Estimate
                  </span>
                </div>

                <div style={{ background: 'var(--success-bg)', padding: '10px', borderRadius: '6px', border: '1px solid var(--primary-border)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--success-text)', fontWeight: 700, textTransform: 'uppercase', display: 'block' }}>
                    Actual Payment
                  </span>
                  <strong style={{ fontSize: '1.2rem', color: 'var(--primary)', display: 'block', marginTop: '2px' }}>
                    ₹ {Number(procurementForm.payment_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </strong>
                  <span style={{ fontSize: '0.68rem', color: 'var(--success-text)', fontWeight: 600 }}>
                    Certified Weighed Payout
                  </span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Quality Grade</label>
                  <select
                    className="form-control"
                    value={procurementForm.quality_grade}
                    onChange={(e) => setProcurementForm(f => ({ ...f, quality_grade: e.target.value }))}
                  >
                    <option value="GRADE_A">Grade A (FAQ Premium)</option>
                    <option value="GRADE_B">Grade B (Standard Commercial)</option>
                    <option value="GRADE_C">Grade C (Sub-standard)</option>
                  </select>
                </div>
                <div>
                  <label className="form-label" style={{ fontSize: '0.8rem' }}>Moisture Content (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-control"
                    value={procurementForm.moisture_pct}
                    onChange={(e) => setProcurementForm(f => ({ ...f, moisture_pct: e.target.value }))}
                  />
                </div>
              </div>

              {/* Quality Evidence (Section 4) */}
              {renderEvidenceSection('QUALITY', 'Quality Measurement Evidence', 'Photo of inspected sample or physical grading.')}

              {/* Moisture Evidence (Section 6) */}
              {renderEvidenceSection('MOISTURE', 'Moisture Measurement Evidence', 'Photo of digital moisture meter reading.')}

              <div>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>Warehouse Bay / Storage Location</label>
                <input
                  type="text"
                  className="form-control"
                  value={procurementForm.warehouse_location}
                  onChange={(e) => setProcurementForm(f => ({ ...f, warehouse_location: e.target.value }))}
                  placeholder="e.g. Bay A-1, Stack 4"
                />
              </div>

              <div>
                <label className="form-label" style={{ fontSize: '0.8rem' }}>Quality Inspection & Tare Notes</label>
                <textarea
                  className="form-control"
                  rows={2}
                  value={procurementForm.notes}
                  onChange={(e) => setProcurementForm(f => ({ ...f, notes: e.target.value }))}
                />
              </div>

              {/* Action Buttons across State-Driven Workflow */}
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setSelectedArrivedBooking(null)}
                >
                  Close
                </button>

                {procurementStep === 'received' && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={submittingProcurement}
                    onClick={() => handleProcessWorkflowStep('RECEIVED')}
                  >
                    {submittingProcurement ? 'Saving...' : '1. Confirm Receipt (RECEIVED)'}
                  </button>
                )}

                {procurementStep === 'quality' && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={submittingProcurement}
                    onClick={() => handleProcessWorkflowStep('QUALITY_CHECKED')}
                  >
                    {submittingProcurement ? 'Saving...' : '2. Record Quality Check'}
                  </button>
                )}

                {procurementStep === 'weighment' && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={submittingProcurement}
                    onClick={() => handleProcessWorkflowStep('WEIGHED')}
                  >
                    {submittingProcurement ? 'Saving...' : '3. Record Weighment (WEIGHED)'}
                  </button>
                )}

                {procurementStep === 'storage' && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={submittingProcurement}
                    onClick={() => handleProcessWorkflowStep('STORED')}
                  >
                    {submittingProcurement ? 'Saving...' : '4. Store Lot & Initiate Payment'}
                  </button>
                )}

                {procurementStep === 'payment' && (
                  <button
                    type="button"
                    className="btn btn-success"
                    disabled={submittingProcurement}
                    onClick={() => handleProcessWorkflowStep('PAID')}
                  >
                    {submittingProcurement ? 'Saving...' : '5. Record Final DBT Payment (PAID)'}
                  </button>
                )}

                {procurementStep === 'complete' && (
                  <span style={{ color: 'var(--success)', fontWeight: 800, padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Check size={18} /> Procurement & Payment Fully Recorded!
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      {/* ENLARGED PHOTO EVIDENCE MODAL */}
      {enlargedImage && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1300,
            padding: '1.5rem'
          }}
          onClick={() => setEnlargedImage(null)}
        >
          <div style={{ position: 'relative', maxWidth: '90vw', maxHeight: '90vh' }} onClick={e => e.stopPropagation()}>
            <button
              onClick={() => setEnlargedImage(null)}
              style={{
                position: 'absolute',
                top: '-40px',
                right: '0',
                background: 'none',
                border: 'none',
                color: '#fff',
                fontSize: '1.5rem',
                cursor: 'pointer'
              }}
            >
              <X size={28} />
            </button>
            <img 
              src={enlargedImage} 
              alt="Enlarged Evidence" 
              style={{ maxWidth: '100%', maxHeight: '85vh', borderRadius: '8px', objectFit: 'contain', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' }} 
            />
          </div>
        </div>
      )}
    </div>
  );
}
