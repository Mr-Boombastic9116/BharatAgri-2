const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_URL) ? import.meta.env.VITE_API_URL : '/api';

function getAuthHeaders() {
  try {
    const userStr = localStorage.getItem('bharatagri_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user && (user.token || user.access_token)) {
        return {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.token || user.access_token}`
        };
      }
    }
  } catch (e) {
    console.error('Error reading auth headers:', e);
  }
  return { 'Content-Type': 'application/json' };
}

// ----------------------------------------------------
// AUTHENTICATION
// ----------------------------------------------------
export async function loginUser(userId, password, role) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, password, role })
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || data.detail || data.error || 'Authentication failed. Please verify credentials.';
    throw new Error(msg);
  }
  return {
    ...data.user,
    token: data.token || data.access_token
  };
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

// ----------------------------------------------------
// FARMERS
// ----------------------------------------------------
export async function registerFarmer(nameOrPayload, mobile, village, userId, password, preferredLanguage) {
  let bodyPayload;
  if (typeof nameOrPayload === 'object' && nameOrPayload !== null) {
    bodyPayload = nameOrPayload;
  } else {
    bodyPayload = {
      name: nameOrPayload,
      mobile,
      village,
      user_id: userId,
      password,
      preferred_language: preferredLanguage
    };
  }

  const res = await fetch(`${API_BASE}/farmers/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bodyPayload)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || data.detail?.message || data.detail || data.error || 'Farmer registration failed';
    throw new Error(msg);
  }
  return data.user;
}

export async function getFarmerProfile(farmerId) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch farmer profile');
  return res.json();
}

// ----------------------------------------------------
// PROCUREMENT CENTRES & SLOTS
// ----------------------------------------------------
export async function registerCentre(centreName, centreId, password, location, contactNumber, operatingDays, openingTime, closingTime, supportedCrops, state = 'Goa', district = 'North Goa') {
  const res = await fetch(`${API_BASE}/centres/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      centre_name: centreName,
      centre_id: centreId,
      password,
      location,
      contact_number: contactNumber,
      operating_days: operatingDays,
      opening_time: openingTime,
      closing_time: closingTime,
      supported_crops: supportedCrops,
      state,
      district
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Centre registration failed');
  return data.user;
}

export async function getCentres(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `${API_BASE}/centres?${query}` : `${API_BASE}/centres`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch procurement centres');
  const data = await res.json();
  return Array.isArray(data) ? data : (data.data || data);
}

export async function getCentreDetails(centreId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}`);
  if (!res.ok) throw new Error('Failed to fetch centre details');
  return res.json();
}

export async function getSlots(centreId, date) {
  const res = await fetch(`${API_BASE}/slots?centre_id=${encodeURIComponent(centreId)}&date=${encodeURIComponent(date)}`);
  if (!res.ok) throw new Error('Failed to fetch available slots');
  return res.json();
}

export async function createSlot(centreId, date, startTime, endTime, maxCapacity) {
  const res = await fetch(`${API_BASE}/slots`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      centre_id: centreId,
      date,
      start_time: startTime,
      end_time: endTime,
      max_capacity: maxCapacity
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to create slot');
  return data.slot || data;
}

export async function updateSlotCapacity(slotId, maxCapacity) {
  const res = await fetch(`${API_BASE}/slots/${encodeURIComponent(slotId)}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ max_capacity: maxCapacity })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to update slot capacity');
  return data;
}

export async function deleteSlot(slotId) {
  const res = await fetch(`${API_BASE}/slots/${encodeURIComponent(slotId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to delete slot');
  return data;
}

export async function copySchedule(centreId, sourceDate, targetDates) {
  const res = await fetch(`${API_BASE}/slots/copy-schedule`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      centre_id: centreId,
      source_date: sourceDate,
      target_dates: targetDates
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to copy schedule');
  return data;
}

// ----------------------------------------------------
// BOOKINGS & QR
// ----------------------------------------------------
export async function bookSlot(farmerId, centreId, slotId, crop, quantity) {
  const res = await fetch(`${API_BASE}/bookings`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      farmer_id: farmerId,
      centre_id: centreId,
      slot_id: slotId,
      crop,
      quantity: parseFloat(quantity)
    })
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || data.detail?.message || data.detail || 'Slot booking failed. Please verify operating day and capacity.';
    throw new Error(msg);
  }
  return data.booking || data.data || data;
}

export async function getFarmerBookings(farmerId) {
  const res = await fetch(`${API_BASE}/bookings/farmer/${encodeURIComponent(farmerId)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch farmer bookings');
  return res.json();
}

export async function getCentreBookings(centreId, date) {
  let url = `${API_BASE}/bookings/centre/${encodeURIComponent(centreId)}`;
  if (date) {
    url += `?date=${encodeURIComponent(date)}`;
  }
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) throw new Error('Failed to fetch centre bookings');
  return res.json();
}

export async function updateBookingStatus(bookingId, status) {
  const res = await fetch(`${API_BASE}/bookings/${encodeURIComponent(bookingId)}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to update booking status');
  return data;
}

export async function verifyQrToken(qrToken, centreId) {
  const res = await fetch(`${API_BASE}/appointments/verify`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ qr_token: qrToken, centre_id: centreId })
  });
  const data = await res.json();
  return data;
}

export async function getStats() {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error('Failed to fetch statistics');
  return res.json();
}

// ----------------------------------------------------
// OPERATING DAYS & CAPACITY
// ----------------------------------------------------
export async function getOperatingConfig(centreId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/operating-config`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch operating config');
  return res.json();
}

export async function updateOperatingConfig(centreId, config) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/operating-config`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(config)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to update operating configuration');
  return data;
}

export async function updateOperatingDays(centreId, operatingDays) {
  const payload = Array.isArray(operatingDays) ? operatingDays.join(',') : operatingDays;
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/operating-days`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ operating_days: payload })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to update operating days');
  return data;
}

export async function addNonOperationalDate(centreId, date, reason) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/non-operational-dates`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ date, reason })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to add non-operational date');
  return data;
}

export async function removeNonOperationalDate(centreId, date) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/non-operational-dates/${encodeURIComponent(date)}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to remove non-operational date');
  return data;
}

export async function getDailyCapacity(centreId, date) {
  const res = await fetch(`${API_BASE}/daily-capacity?centre_id=${encodeURIComponent(centreId)}&date=${encodeURIComponent(date)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch daily capacity');
  return res.json();
}

export async function updateDailyCapacity(centreId, date, maxQuintalsPerDay) {
  const res = await fetch(`${API_BASE}/daily-capacity`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ centre_id: centreId, date, max_quintals_per_day: maxQuintalsPerDay })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to update daily capacity');
  return data;
}

export async function applyScheduleRange(centreId, startDate, endDate, timeSlots, maxQuintalsPerDay) {
  const res = await fetch(`${API_BASE}/slots/apply-schedule-range`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      centre_id: centreId,
      start_date: startDate,
      end_date: endDate,
      time_slots: timeSlots,
      max_quintals_per_day: maxQuintalsPerDay
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.error || 'Failed to apply schedule range');
  return data;
}

// ----------------------------------------------------
// PROCUREMENT TRACEABILITY LIFECYCLE
// ----------------------------------------------------
export async function recordCollection(payload) {
  const res = await fetch(`${API_BASE}/procurement/collection`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Collection recording failed');
  return data;
}

export async function recordQualityCheck(payload) {
  const res = await fetch(`${API_BASE}/procurement/quality`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Quality check recording failed');
  return data;
}

export async function recordWeighment(payload) {
  const res = await fetch(`${API_BASE}/procurement/weighment`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Weighment recording failed');
  return data;
}

export async function recordProcurement(payload) {
  const res = await fetch(`${API_BASE}/procurement/procure`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Procurement finalization failed');
  return data;
}

export async function getTraceabilityLot(lotOrId) {
  const res = await fetch(`${API_BASE}/procurement/traceability/${encodeURIComponent(lotOrId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Lot traceability record not found');
  return data.data || data;
}

export async function getProcurementLots(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/procurement/lots?${query}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch procurement lots');
  return res.json();
}

export async function completePayment(paymentId, bankRefNumber) {
  const res = await fetch(`${API_BASE}/procurement/payment/${encodeURIComponent(paymentId)}/complete`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ bank_ref_number: bankRefNumber })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to complete payment');
  return data;
}

// ----------------------------------------------------
// PHOTO EVIDENCE (QUALITY, WEIGHING, MOISTURE)
// ----------------------------------------------------
export async function uploadProcurementEvidence(formData) {
  let authHeader = {};
  try {
    const userStr = localStorage.getItem('bharatagri_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user && (user.token || user.access_token)) {
        authHeader['Authorization'] = `Bearer ${user.token || user.access_token}`;
      }
    }
  } catch (e) {
    console.error('Error resolving auth token for evidence upload:', e);
  }

  const res = await fetch(`${API_BASE}/procurement/evidence/upload`, {
    method: 'POST',
    headers: authHeader,
    body: formData
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to upload photo evidence');
  return data;
}

export async function getProcurementEvidence(bookingId) {
  const res = await fetch(`${API_BASE}/procurement/evidence/${encodeURIComponent(bookingId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to retrieve photo evidence');
  return data;
}

// ----------------------------------------------------
// SEQUENTIAL 5-STEP PROCUREMENT WORKFLOW & MANGO AI SCAN
// ----------------------------------------------------
export async function getProcurementProcessState(appointmentId) {
  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/state`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to load procurement process state');
  return data;
}

export async function submitProcurementProcessStep(appointmentId, stepNumber, stepData = {}, notes = '') {
  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/step/${stepNumber}/submit`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ step_number: stepNumber, data: stepData, notes })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || `Failed to submit Step ${stepNumber}`);
  return data;
}

export async function applyProcurementStepCorrection(appointmentId, stepNumber, fieldName, newValue, correctionReason) {
  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/correction`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      step_number: stepNumber,
      field_name: fieldName,
      new_value: String(newValue),
      correction_reason: correctionReason
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to submit step correction');
  return data;
}

export async function recordStorageFinalCheck(appointmentId, payload) {
  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/storage-check`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Storage check failed');
  return data;
}

export async function uploadProcessEvidence(appointmentId, formData) {
  let authHeader = {};
  try {
    const userStr = localStorage.getItem('bharatagri_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user && (user.token || user.access_token)) {
        authHeader['Authorization'] = `Bearer ${user.token || user.access_token}`;
      }
    }
  } catch (e) {
    console.error('Error resolving auth token for process evidence:', e);
  }

  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/evidence`, {
    method: 'POST',
    headers: authHeader,
    body: formData
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to upload photo evidence');
  return data;
}

export async function scanMangoQuality(appointmentId, imageFile) {
  let authHeader = {};
  try {
    const userStr = localStorage.getItem('bharatagri_user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user && (user.token || user.access_token)) {
        authHeader['Authorization'] = `Bearer ${user.token || user.access_token}`;
      }
    }
  } catch (e) {
    console.error('Error resolving token for mango scan:', e);
  }

  const formData = new FormData();
  formData.append('appointment_id', appointmentId);
  formData.append('file', imageFile);

  const res = await fetch(`${API_BASE}/procurement/quality/mango-scan`, {
    method: 'POST',
    headers: authHeader,
    body: formData
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Mango AI scan failed');
  return data;
}

// AI & OPTIMIZATION ENGINES
// ----------------------------------------------------
export async function getSupplyForecast(payload) {
  const res = await fetch(`${API_BASE}/ai/supply-forecast`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Supply forecast calculation failed');
  return data.data || data;
}

export async function getCongestionLevels(centreId, date) {
  let url = `${API_BASE}/ai/congestion`;
  const params = [];
  if (centreId) params.push(`centre_id=${encodeURIComponent(centreId)}`);
  if (date) params.push(`calculation_date=${encodeURIComponent(date)}`);
  if (params.length) url += `?${params.join('&')}`;

  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to fetch congestion levels');
  return data.data || data;
}

export async function optimizeTruckDispatch(payload) {
  const res = await fetch(`${API_BASE}/ai/truck-allocation`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Optimization solver failed');
  return data;
}

export async function getAnomalies(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/ai/anomalies?${query}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch anomalies');
  return data.data || data;
}

export async function updateAnomalyStatus(anomalyId, status, notes) {
  const res = await fetch(`${API_BASE}/ai/anomalies/${encodeURIComponent(anomalyId)}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status, notes })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to update anomaly status');
  return data;
}

export async function getBardanForecast(centreId) {
  let url = `${API_BASE}/bardan/forecast`;
  if (centreId) url += `?centre_id=${encodeURIComponent(centreId)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch bardan forecast');
  return data.data || data;
}

export async function getBardanStock(centreId) {
  let url = `${API_BASE}/bardan/stock`;
  if (centreId) url += `?centre_id=${encodeURIComponent(centreId)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  return res.json();
}

export async function getTrucks(centreId) {
  let url = `${API_BASE}/trucks`;
  if (centreId) url += `?centre_id=${encodeURIComponent(centreId)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  return data.data || data;
}

export async function createTruckRequest(payload) {
  const res = await fetch(`${API_BASE}/trucks/request`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  return res.json();
}

// ----------------------------------------------------
// GOVERNMENT ANALYTICS & MONITORING
// ----------------------------------------------------
export async function getGovernmentKPIs() {
  const res = await fetch(`${API_BASE}/government/kpis`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to load Government KPIs');
  return data.data || data;
}

export async function getProcurementTrend(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/procurement-trend${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getCropDistribution(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/crop-distribution${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getGeographyProcurement(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/state-district-procurement${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getForecastVsActual(paramsOrState) {
  let query = '';
  if (typeof paramsOrState === 'string') {
    query = paramsOrState && paramsOrState !== 'Nationwide' ? `?state=${encodeURIComponent(paramsOrState)}` : '';
  } else if (paramsOrState && typeof paramsOrState === 'object') {
    const q = new URLSearchParams();
    if (paramsOrState.state && paramsOrState.state !== 'Nationwide') q.append('state', paramsOrState.state);
    if (paramsOrState.crop && paramsOrState.crop !== 'ALL') q.append('crop', paramsOrState.crop);
    if (paramsOrState.district && paramsOrState.district !== 'ALL') q.append('district', paramsOrState.district);
    query = q.toString() ? `?${q.toString()}` : '';
  }
  const res = await fetch(`${API_BASE}/government/analytics/forecast-vs-actual${query}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getCentreUtilizationAnalytics(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/centre-utilization${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getPaymentsSummary(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/payments-summary${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getAnomaliesSummary(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/anomalies-summary${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || {};
}

export async function getGovernmentCentres(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/centres${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return Array.isArray(data) ? data : (data.data || []);
}

export async function getGovernmentCentreDetail(centreId) {
  const res = await fetch(`${API_BASE}/government/centres/${encodeURIComponent(centreId)}/detail`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to fetch centre detail');
  return data.data || data;
}

// ----------------------------------------------------
// COMPLAINTS / GRIEVANCE REDRESSAL
// ----------------------------------------------------
export async function getComplaints(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/complaints?${query}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getComplaintDetails(complaintId) {
  const res = await fetch(`${API_BASE}/complaints/${encodeURIComponent(complaintId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || data;
}

export async function createComplaint(payload) {
  const res = await fetch(`${API_BASE}/complaints`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to submit complaint');
  return data.data || data;
}

export async function sendComplaintMessage(complaintId, message) {
  const res = await fetch(`${API_BASE}/complaints/${encodeURIComponent(complaintId)}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ message })
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to post reply');
  return data;
}

export async function updateComplaintStatus(complaintId, status, resolution) {
  const res = await fetch(`${API_BASE}/complaints/${encodeURIComponent(complaintId)}/status`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ status, resolution })
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to update complaint status');
  return data;
}

// ----------------------------------------------------
// AGENT WORKFLOWS
// ----------------------------------------------------
export async function getAssignedFarmers() {
  const res = await fetch(`${API_BASE}/agents/farmers`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || data;
}

export async function registerFarmerByAgent(payload) {
  const res = await fetch(`${API_BASE}/agents/farmers/register`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Agent registration of farmer failed');
  return data;
}

// ----------------------------------------------------
// GOVERNMENT — STATE FILTER SUPPORT
// ----------------------------------------------------
export async function getAvailableStates() {
  const res = await fetch(`${API_BASE}/government/states`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.states || [];
}

export async function getGovernmentKPIsWithState(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/kpis${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to load Government KPIs');
  return data.data || data;
}

export async function getProcurementTrendWithState(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/procurement-trend${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getCropDistributionWithState(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/crop-distribution${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function getGeographyProcurementWithState(state) {
  const params = state && state !== 'Nationwide' ? `?state=${encodeURIComponent(state)}` : '';
  const res = await fetch(`${API_BASE}/government/analytics/state-district-procurement${params}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

// ----------------------------------------------------
// PRICE & MSP INTELLIGENCE
// ----------------------------------------------------
export async function getMspPrices(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/price/msp?${query}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || data;
}

export async function getEstimatedPrice(payload) {
  const res = await fetch(`${API_BASE}/price/estimate`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Price estimation failed');
  return data.data || data;
}

export async function getPriceIntelligence(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `${API_BASE}/price-intelligence?${query}` : `${API_BASE}/price-intelligence`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  return data;
}

export async function getStateCropSupplyDemand(state) {
  let url = `${API_BASE}/price-intelligence`;
  if (state && state !== 'Nationwide') url += `?state=${encodeURIComponent(state)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  return data.data || data;
}

export async function getCentreOperationalIntelligence(centreId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/operational-intelligence`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error('Failed to fetch centre operational intelligence');
  const data = await res.json();
  return data;
}

// ----------------------------------------------------
// TRUCK ROUTES & GOVERNMENT APPROVAL
// ----------------------------------------------------
export async function getTruckRoutePredictions(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/trucks/routes/predictions?${query}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  return data.data || [];
}

export async function generateTruckRoutePredictions(payload = {}) {
  const res = await fetch(`${API_BASE}/trucks/routes/predict`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  return data;
}

export async function approveTruckRoute(routeId, comments) {
  const res = await fetch(`${API_BASE}/trucks/routes/${encodeURIComponent(routeId)}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ comments: comments || '' })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Approval failed');
  return data;
}

export async function rejectTruckRoute(routeId, reason, comments) {
  const res = await fetch(`${API_BASE}/trucks/routes/${encodeURIComponent(routeId)}/reject`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ rejection_reason: reason, comments: comments || '' })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Rejection failed');
  return data;
}

export async function scheduleTruckRoute(routeId) {
  const res = await fetch(`${API_BASE}/trucks/routes/${encodeURIComponent(routeId)}/schedule`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Scheduling failed');
  return data;
}

export async function updateTruckRoute(routeId, payload) {
  const res = await fetch(`${API_BASE}/trucks/routes/${encodeURIComponent(routeId)}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Update failed');
  return data;
}

// ----------------------------------------------------
// FARMER CROPS CRUD
// ----------------------------------------------------
export async function getFarmerCrops(farmerId) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}/crops`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch farmer crops');
  return Array.isArray(data) ? data : (data.data || []);
}

export async function addFarmerCrop(farmerId, payload) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}/crops`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to add crop');
  return data.crop || data;
}

export async function updateFarmerCrop(farmerId, cropId, payload) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}/crops/${cropId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to update crop');
  return data.crop || data;
}

export async function deleteFarmerCrop(farmerId, cropId) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}/crops/${cropId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to delete crop');
  return data;
}

export async function updateFarmerProfile(farmerId, payload) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error?.message || data.detail || 'Failed to update profile');
  return data.farmer || data;
}

// ----------------------------------------------------
// AGENT & GOVERNMENT REGISTRATION
// ----------------------------------------------------
export async function registerAgent(payload) {
  const res = await fetch(`${API_BASE}/agents/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || data.detail?.message || data.detail || data.error || 'Agent registration failed';
    throw new Error(msg);
  }
  return data;
}

export async function registerGovernment(payload) {
  const res = await fetch(`${API_BASE}/government/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = data.error?.message || data.detail?.message || data.detail || data.error || 'Government registration failed';
    throw new Error(msg);
  }
  return data;
}

// ----------------------------------------------------
// AI PRICE ESTIMATION & PERISHABLE CROPS
// ----------------------------------------------------
export async function getCropMetadata(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `${API_BASE}/crops/metadata?${query}` : `${API_BASE}/crops/metadata`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch crop metadata');
  return data.data || [];
}

export async function estimatePrice(payload) {
  const res = await fetch(`${API_BASE}/price/estimate`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to estimate price');
  return data;
}

export async function getTransportPriority(payload) {
  const res = await fetch(`${API_BASE}/logistics/transport-priority`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to calculate transport priority');
  return data;
}

// ----------------------------------------------------
// CENTRE INTELLIGENCE, REDIRECTION & ALERTS
// ----------------------------------------------------
export async function getCentreRedirectionOptions(centreId, crop = '', quantity = 0) {
  let url = `${API_BASE}/centres/${encodeURIComponent(centreId)}/redirection-options`;
  const params = new URLSearchParams();
  if (crop) params.append('crop', crop);
  if (quantity) params.append('quantity', quantity);
  const qStr = params.toString();
  if (qStr) url += `?${qStr}`;

  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch redirection options');
  return data;
}

export async function getCentreAlerts(centreId, severity = '') {
  let url = `${API_BASE}/centres/${encodeURIComponent(centreId)}/alerts`;
  if (severity) url += `?severity=${encodeURIComponent(severity)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch centre alerts');
  return data.data || [];
}

export async function getCentreInsights(centreId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/insights`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch centre insights');
  return data;
}

export async function getCentreDailyIntelligence(centreId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/daily-intelligence`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch centre daily intelligence');
  return data;
}

export async function resolveAlert(alertId, resolutionNotes = '') {
  const res = await fetch(`${API_BASE}/alerts/${encodeURIComponent(alertId)}/resolve`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ resolution_notes: resolutionNotes })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to resolve alert');
  return data;
}

// ----------------------------------------------------
// GOVERNMENT ALERTS, INSIGHTS & DAILY INTELLIGENCE
// ----------------------------------------------------
export async function getGovernmentAlerts(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `${API_BASE}/government/alerts?${query}` : `${API_BASE}/government/alerts`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch government alerts');
  return data.data || [];
}

export async function getGovernmentInsights(state = '') {
  let url = `${API_BASE}/government/insights`;
  if (state && state.toLowerCase() !== 'all') url += `?state=${encodeURIComponent(state)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch government insights');
  return data;
}

export async function getGovernmentDailyIntelligence(state = '') {
  let url = `${API_BASE}/government/daily-intelligence`;
  if (state && state.toLowerCase() !== 'all') url += `?state=${encodeURIComponent(state)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch government daily intelligence');
  return data;
}

export async function getGovernmentPerishablePriority(state = '') {
  let url = `${API_BASE}/government/perishable-priority`;
  if (state && state.toLowerCase() !== 'all') url += `?state=${encodeURIComponent(state)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch perishable crop transport priorities');
  return data.data || [];
}

// ----------------------------------------------------
// FARMER WORKFLOW TRACKER & MARKET INTELLIGENCE
// ----------------------------------------------------
export async function getBookingWorkflowStatus(bookingId) {
  const res = await fetch(`${API_BASE}/bookings/${encodeURIComponent(bookingId)}/workflow-status`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch booking workflow status');
  return data;
}

export async function getFarmerMarketIntelligence(farmerId) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}/market-intelligence`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch farmer market intelligence');
  return data;
}

export async function getFarmerDailyIntelligence(farmerId) {
  const res = await fetch(`${API_BASE}/farmers/${encodeURIComponent(farmerId)}/daily-intelligence`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error('Failed to fetch farmer daily intelligence');
  return data;
}

// ----------------------------------------------------
// PROCUREMENT CENTRE EMPLOYEES (Requirement 2)
// ----------------------------------------------------
export async function getCentreEmployees(centreId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/employees`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch centre employees');
  return data.data || [];
}

export async function addCentreEmployee(centreId, payload) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/employees`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to add centre employee');
  return data;
}

export async function deleteCentreEmployee(centreId, employeeId) {
  const res = await fetch(`${API_BASE}/centres/${encodeURIComponent(centreId)}/employees/${encodeURIComponent(employeeId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to delete centre employee');
  return data;
}

// ----------------------------------------------------
// DEDICATED STORAGE & EVIDENCE
// ----------------------------------------------------
export async function submitStorageFinalCheck(appointmentId, payload) {
  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/storage-check`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to submit storage final check');
  return data;
}

export async function uploadProcessStepEvidence(appointmentId, file, processStep = 'STORAGE', evidenceType = 'STORAGE_FINAL_CHECK', notes = '') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('process_step', processStep);
  formData.append('evidence_type', evidenceType);
  if (notes) formData.append('notes', notes);

  const token = localStorage.getItem('token');
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/procurement/process/${encodeURIComponent(appointmentId)}/evidence`, {
    method: 'POST',
    headers,
    body: formData
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to upload step evidence');
  return data;
}

// ----------------------------------------------------
// DYNAMIC AI QUEUE & SIH INTELLIGENCE
// ----------------------------------------------------
export async function getLiveQueue(centreId) {
  const res = await fetch(`${API_BASE}/queue/live/${encodeURIComponent(centreId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch live queue');
  return data.data;
}

export async function trackToken(tokenOrId) {
  const res = await fetch(`${API_BASE}/queue/token/${encodeURIComponent(tokenOrId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to track token');
  return data.data;
}

export async function recommendCentre(payload) {
  const res = await fetch(`${API_BASE}/queue/recommend-centre`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch centre recommendations');
  return data;
}

export async function getRecommendedSlots(centreId, date) {
  const url = date ? `${API_BASE}/queue/recommended-slots/${encodeURIComponent(centreId)}?date=${encodeURIComponent(date)}` : `${API_BASE}/queue/recommended-slots/${encodeURIComponent(centreId)}`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch recommended slots');
  return data;
}

export async function getCongestionForecast(centreId) {
  const res = await fetch(`${API_BASE}/queue/congestion-forecast/${encodeURIComponent(centreId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch congestion forecast');
  return data.data;
}

export async function getFarmerOverview(farmerId) {
  const res = await fetch(`${API_BASE}/queue/farmer-overview/${encodeURIComponent(farmerId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch farmer overview');
  return data;
}

export async function getFarmerNotifications(farmerId) {
  const res = await fetch(`${API_BASE}/queue/notifications/${encodeURIComponent(farmerId)}`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch farmer notifications');
  return data.notifications || [];
}

export async function queryCopilot(query) {
  const res = await fetch(`${API_BASE}/queue/copilot`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ query })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to query copilot');
  return data.data;
}

export async function queryCentreCopilot(centreId, query) {
  const res = await fetch(`${API_BASE}/queue/centre-copilot/${encodeURIComponent(centreId)}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ query })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to query centre copilot');
  return data.data;
}


export async function getOperationalAnomalies() {
  const res = await fetch(`${API_BASE}/queue/anomalies`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch anomalies');
  return data;
}

export async function getCropsMaster() {
  const res = await fetch(`${API_BASE}/queue/crops-master`, {
    headers: getAuthHeaders()
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail?.message || data.detail || 'Failed to fetch crops master');
  return data.crops || [];
}


