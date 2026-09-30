const express = require('express');
const cors = require('cors');
const { initDatabase, runAsync, getAsync, allAsync } = require('./db');
const seedData = require('./seed');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Initialize Database & Seed only if database is completely empty
initDatabase().then(async () => {
  try {
    const userCount = await getAsync(`SELECT COUNT(*) as count FROM USERS`);
    if (!userCount || userCount.count === 0) {
      await seedData();
    }
  } catch (err) {
    console.error('Database startup check error:', err);
  }
});

// Helper to generate Appointment ID (Format: PF-260915-042)
async function generateAppointmentId(dateStr) {
  const cleanDate = dateStr ? dateStr.replace(/-/g, '').substring(2) : '260915';
  const randomSeq = Math.floor(100 + Math.random() * 900);
  const appointment_id = `PF-${cleanDate}-${randomSeq}`;

  const existing = await getAsync(`SELECT id FROM BOOKINGS WHERE appointment_id = ?`, [appointment_id]);
  if (existing) {
    return generateAppointmentId(dateStr);
  }
  return appointment_id;
}

function generateQrToken(appointmentId) {
  return `BA-QR-${appointmentId}`;
}

const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function getDayName(dateString) {
  const d = new Date(dateString);
  return dayNames[d.getDay()];
}

// ----------------------------------------------------
// 1. AUTHENTICATION ENDPOINTS
// ----------------------------------------------------

app.post('/api/auth/login', async (req, res) => {
  try {
    const { user_id, password, role } = req.body;

    if (!user_id || !password || !role) {
      return res.status(400).json({ error: 'Please provide User ID, Password, and Role.' });
    }

    const user = await getAsync(
      `SELECT * FROM USERS WHERE LOWER(user_id) = LOWER(?) AND role = ?`,
      [user_id.trim(), role]
    );

    if (!user || user.password !== password) {
      return res.status(401).json({ error: 'Invalid User ID or Password for the selected role.' });
    }

    res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        name: user.name,
        mobile: user.mobile,
        village: user.village,
        user_id: user.user_id,
        preferred_language: user.preferred_language || 'English',
        role: user.role
      }
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ error: 'Server error during login.' });
  }
});

// POST /api/farmers/register
app.post('/api/farmers/register', async (req, res) => {
  try {
    const { name, mobile, village, user_id, password, preferred_language } = req.body;

    if (!name || !user_id || !password || !mobile || !village) {
      return res.status(400).json({ error: 'Name, Mobile Number, Village, Farmer ID, and Password are required.' });
    }

    const existing = await getAsync(`SELECT id FROM USERS WHERE LOWER(user_id) = LOWER(?)`, [user_id.trim()]);
    if (existing) {
      return res.status(400).json({ error: 'Farmer ID already exists. Please choose a different ID.' });
    }

    await runAsync(
      `INSERT INTO USERS (name, mobile, village, user_id, password, preferred_language, role) VALUES (?, ?, ?, ?, ?, ?, 'farmer')`,
      [name.trim(), mobile.trim(), village.trim(), user_id.trim(), password, preferred_language || 'English']
    );

    res.status(201).json({
      message: 'Farmer registered successfully',
      user: {
        name: name.trim(),
        mobile: mobile.trim(),
        village: village.trim(),
        user_id: user_id.trim(),
        preferred_language: preferred_language || 'English',
        role: 'farmer'
      }
    });
  } catch (err) {
    console.error('Farmer registration error:', err);
    res.status(500).json({ error: 'Server error during registration.' });
  }
});

// POST /api/centres/register
app.post('/api/centres/register', async (req, res) => {
  try {
    const { centre_name, centre_id, password, location, contact_number, operating_days, opening_time, closing_time, supported_crops } = req.body;

    if (!centre_name || !centre_name.trim()) {
      return res.status(400).json({ error: 'Centre Name is required.' });
    }

    if (!centre_id || !centre_id.trim()) {
      return res.status(400).json({ error: 'Centre ID is required.' });
    }

    if (!password || !password.trim()) {
      return res.status(400).json({ error: 'Password is required.' });
    }

    const existingUser = await getAsync(`SELECT id FROM USERS WHERE LOWER(user_id) = LOWER(?)`, [centre_id.trim()]);
    if (existingUser) {
      return res.status(400).json({ error: 'Centre ID is already registered.' });
    }

    let days = 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday';
    if (operating_days) {
      days = Array.isArray(operating_days)
        ? operating_days.map(d => String(d).trim()).filter(Boolean).join(',')
        : String(operating_days).trim();
    }
    const crops = supported_crops || 'Paddy,Wheat,Maize,Cotton';
    const loc = location || 'Main Market Yard';
    const contact = contact_number || '9876543210';
    const openTime = opening_time || '09:00 AM';
    const closeTime = closing_time || '05:00 PM';

    await runAsync(
      `INSERT INTO PROCUREMENT_CENTRES (centre_name, centre_id, location, contact_number, operating_days, opening_time, closing_time, supported_crops)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [centre_name.trim(), centre_id.trim(), loc, contact, days, openTime, closeTime, crops]
    );

    await runAsync(
      `INSERT INTO USERS (name, user_id, password, role) VALUES (?, ?, ?, 'centre')`,
      [centre_name.trim(), centre_id.trim(), password]
    );

    res.status(201).json({
      message: 'Procurement Centre registered successfully',
      user: {
        name: centre_name.trim(),
        user_id: centre_id.trim(),
        location: loc,
        contact_number: contact,
        operating_days: days,
        opening_time: openTime,
        closing_time: closeTime,
        supported_crops: crops,
        role: 'centre'
      }
    });
  } catch (err) {
    console.error('Centre registration error:', err);
    res.status(500).json({ error: 'Server error during centre registration.' });
  }
});

// ----------------------------------------------------
// 2. PROCUREMENT CENTRES, OPERATING DAYS & HOLIDAYS
// ----------------------------------------------------

app.get('/api/centres', async (req, res) => {
  try {
    const centres = await allAsync(`SELECT * FROM PROCUREMENT_CENTRES ORDER BY centre_name ASC`);
    res.json(centres);
  } catch (err) {
    console.error('Fetch centres error:', err);
    res.status(500).json({ error: 'Error fetching procurement centres.' });
  }
});

app.get('/api/centres/:id', async (req, res) => {
  try {
    const centre = await getAsync(`SELECT * FROM PROCUREMENT_CENTRES WHERE centre_id = ?`, [req.params.id]);
    if (!centre) return res.status(404).json({ error: 'Centre not found.' });
    res.json(centre);
  } catch (err) {
    res.status(500).json({ error: 'Error fetching centre details.' });
  }
});

// GET /api/centres/:id/operating-config
app.get('/api/centres/:id/operating-config', async (req, res) => {
  try {
    const centre_id = req.params.id;
    const centre = await getAsync(`SELECT operating_days, opening_time, closing_time FROM PROCUREMENT_CENTRES WHERE centre_id = ?`, [centre_id]);
    const exceptions = await allAsync(`SELECT id, date, reason FROM NON_OPERATIONAL_DATES WHERE centre_id = ? ORDER BY date ASC`, [centre_id]);

    let opDays = centre && centre.operating_days ? centre.operating_days : 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday';
    if (opDays === '[object Object]') {
      opDays = 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday';
    }

    res.json({
      centre_id,
      operating_days: opDays,
      opening_time: centre ? centre.opening_time : '09:00 AM',
      closing_time: centre ? centre.closing_time : '05:00 PM',
      non_operational_dates: exceptions
    });
  } catch (err) {
    console.error('Operating config error:', err);
    res.status(500).json({ error: 'Error fetching operating configuration.' });
  }
});

// PUT /api/centres/:id/operating-days
app.put('/api/centres/:id/operating-days', async (req, res) => {
  try {
    const centre_id = req.params.id;
    const { operating_days } = req.body;

    if (operating_days === undefined || operating_days === null) {
      return res.status(400).json({ error: 'operating_days is required.' });
    }

    let formattedDays = '';
    if (Array.isArray(operating_days)) {
      formattedDays = operating_days.map(d => String(d).trim()).filter(Boolean).join(',');
    } else if (typeof operating_days === 'string') {
      formattedDays = operating_days.trim();
    } else {
      return res.status(400).json({ error: 'Invalid operating_days format.' });
    }

    if (!formattedDays) {
      return res.status(400).json({ error: 'operating_days cannot be empty.' });
    }

    await runAsync(`UPDATE PROCUREMENT_CENTRES SET operating_days = ? WHERE centre_id = ?`, [formattedDays, centre_id]);

    res.json({ message: 'Operating days updated successfully.', operating_days: formattedDays });
  } catch (err) {
    console.error('Update operating days error:', err);
    res.status(500).json({ error: 'Error updating operating days.' });
  }
});

// POST /api/centres/:id/non-operational-dates
app.post('/api/centres/:id/non-operational-dates', async (req, res) => {
  try {
    const centre_id = req.params.id;
    const { date, reason } = req.body;

    if (!date) {
      return res.status(400).json({ error: 'Date is required for non-operational exception.' });
    }

    // Check if active bookings exist for date
    const activeBookings = await getAsync(
      `SELECT COUNT(*) as count FROM BOOKINGS WHERE centre_id = ? AND slot_id IN (SELECT id FROM SLOTS WHERE date = ?) AND status != 'REJECTED'`,
      [centre_id, date]
    );

    if (activeBookings && activeBookings.count > 0) {
      return res.status(400).json({
        error: `Cannot mark ${date} non-operational because ${activeBookings.count} active farmer bookings exist.`
      });
    }

    await runAsync(
      `INSERT OR REPLACE INTO NON_OPERATIONAL_DATES (centre_id, date, reason) VALUES (?, ?, ?)`,
      [centre_id, date, reason || 'Non-operational date']
    );

    res.status(201).json({ message: `Non-operational date ${date} added successfully.`, date, reason });
  } catch (err) {
    console.error('Add non-operational date error:', err);
    res.status(500).json({ error: 'Error adding non-operational date.' });
  }
});

// DELETE /api/centres/:id/non-operational-dates/:date
app.delete('/api/centres/:id/non-operational-dates/:date', async (req, res) => {
  try {
    const { id, date } = req.params;
    await runAsync(`DELETE FROM NON_OPERATIONAL_DATES WHERE centre_id = ? AND date = ?`, [id, date]);
    res.json({ message: `Non-operational exception for ${date} removed.` });
  } catch (err) {
    console.error('Remove non-operational date error:', err);
    res.status(500).json({ error: 'Error removing non-operational date.' });
  }
});

// ----------------------------------------------------
// 3. DAILY QUINTAL CAPACITY API
// ----------------------------------------------------

// GET /api/daily-capacity
app.get('/api/daily-capacity', async (req, res) => {
  try {
    const { centre_id, date } = req.query;

    if (!centre_id || !date) {
      return res.status(400).json({ error: 'centre_id and date are required.' });
    }

    const capRow = await getAsync(`SELECT max_quintals_per_day FROM DAILY_CAPACITY WHERE centre_id = ? AND date = ?`, [centre_id, date]);
    const max_quintals = capRow ? capRow.max_quintals_per_day : 500;

    const sumRow = await getAsync(
      `SELECT SUM(b.quantity) as total_quintals FROM BOOKINGS b
       JOIN SLOTS s ON b.slot_id = s.id
       WHERE b.centre_id = ? AND s.date = ? AND b.status != 'REJECTED'`,
      [centre_id, date]
    );

    const booked_quintals = sumRow && sumRow.total_quintals ? sumRow.total_quintals : 0;
    const remaining_quintals = Math.max(0, max_quintals - booked_quintals);

    res.json({
      centre_id,
      date,
      max_quintals_per_day: max_quintals,
      booked_quintals,
      remaining_quintals,
      is_full: remaining_quintals <= 0
    });
  } catch (err) {
    console.error('Daily capacity error:', err);
    res.status(500).json({ error: 'Error fetching daily capacity.' });
  }
});

// PUT /api/daily-capacity
app.put('/api/daily-capacity', async (req, res) => {
  try {
    const { centre_id, date, max_quintals_per_day } = req.body;

    if (!centre_id || !date || !max_quintals_per_day) {
      return res.status(400).json({ error: 'centre_id, date, and max_quintals_per_day are required.' });
    }

    const maxQ = parseFloat(max_quintals_per_day);
    if (isNaN(maxQ) || maxQ <= 0) {
      return res.status(400).json({ error: 'Daily capacity must be a positive number.' });
    }

    // Check booked quintals
    const sumRow = await getAsync(
      `SELECT SUM(b.quantity) as total_quintals FROM BOOKINGS b
       JOIN SLOTS s ON b.slot_id = s.id
       WHERE b.centre_id = ? AND s.date = ? AND b.status != 'REJECTED'`,
      [centre_id, date]
    );

    const booked_quintals = sumRow && sumRow.total_quintals ? sumRow.total_quintals : 0;

    if (maxQ < booked_quintals) {
      return res.status(400).json({
        error: `Cannot reduce daily capacity below the quantity already booked (${booked_quintals} Quintals booked).`
      });
    }

    await runAsync(
      `INSERT OR REPLACE INTO DAILY_CAPACITY (centre_id, date, max_quintals_per_day) VALUES (?, ?, ?)`,
      [centre_id, date, maxQ]
    );

    res.json({
      message: 'Daily capacity updated successfully',
      centre_id,
      date,
      max_quintals_per_day: maxQ,
      booked_quintals,
      remaining_quintals: maxQ - booked_quintals
    });
  } catch (err) {
    console.error('Update daily capacity error:', err);
    res.status(500).json({ error: 'Error updating daily capacity.' });
  }
});

// ----------------------------------------------------
// 4. TIME SLOTS & DATE RANGE SCHEDULE CREATION
// ----------------------------------------------------

app.get('/api/slots', async (req, res) => {
  try {
    const { centre_id, date } = req.query;

    if (!centre_id || !date) {
      return res.status(400).json({ error: 'centre_id and date query parameters are required.' });
    }

    const slots = await allAsync(
      `SELECT s.*, 
        (SELECT COUNT(*) FROM BOOKINGS b WHERE b.slot_id = s.id AND b.status != 'REJECTED') as booked_count
       FROM SLOTS s
       WHERE s.centre_id = ? AND s.date = ?
       ORDER BY s.id ASC`,
      [centre_id, date]
    );

    const formattedSlots = slots.map(s => {
      const remaining = s.max_capacity - s.booked_count;
      let statusLabel = 'Available';
      if (remaining <= 0) {
        statusLabel = 'Full';
      } else if (s.booked_count > 0) {
        statusLabel = 'Partially Booked';
      }

      return {
        id: s.id,
        centre_id: s.centre_id,
        date: s.date,
        start_time: s.start_time,
        end_time: s.end_time,
        max_capacity: s.max_capacity,
        booked_count: s.booked_count,
        remaining_capacity: Math.max(0, remaining),
        status_label: statusLabel,
        is_full: remaining <= 0
      };
    });

    res.json(formattedSlots);
  } catch (err) {
    console.error('Fetch slots error:', err);
    res.status(500).json({ error: 'Error fetching time slots.' });
  }
});

app.post('/api/slots', async (req, res) => {
  try {
    const { centre_id, date, start_time, end_time, max_capacity } = req.body;

    if (!centre_id || !date || !start_time || !end_time || !max_capacity) {
      return res.status(400).json({ error: 'All slot fields are required.' });
    }

    const cap = parseInt(max_capacity, 10);
    if (isNaN(cap) || cap <= 0) {
      return res.status(400).json({ error: 'Maximum capacity must be a positive number.' });
    }

    const existing = await getAsync(
      `SELECT id FROM SLOTS WHERE centre_id = ? AND date = ? AND start_time = ? AND end_time = ?`,
      [centre_id, date, start_time, end_time]
    );
    if (existing) {
      return res.status(400).json({ error: `A slot for ${start_time} - ${end_time} already exists on ${date}.` });
    }

    const result = await runAsync(
      `INSERT INTO SLOTS (centre_id, date, start_time, end_time, max_capacity) VALUES (?, ?, ?, ?, ?)`,
      [centre_id, date, start_time, end_time, cap]
    );

    res.status(201).json({
      message: 'Slot created successfully',
      slot: {
        id: result.lastID,
        centre_id,
        date,
        start_time,
        end_time,
        max_capacity: cap,
        booked_count: 0,
        remaining_capacity: cap,
        status_label: 'Available',
        is_full: false
      }
    });
  } catch (err) {
    console.error('Create slot error:', err);
    res.status(500).json({ error: 'Error creating slot.' });
  }
});

app.put('/api/slots/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { max_capacity } = req.body;

    const cap = parseInt(max_capacity, 10);
    if (isNaN(cap) || cap <= 0) {
      return res.status(400).json({ error: 'Maximum capacity must be a positive number.' });
    }

    const slot = await getAsync(`SELECT * FROM SLOTS WHERE id = ?`, [id]);
    if (!slot) {
      return res.status(404).json({ error: 'Slot not found.' });
    }

    const bookedCountRow = await getAsync(
      `SELECT COUNT(*) as count FROM BOOKINGS WHERE slot_id = ? AND status != 'REJECTED'`,
      [id]
    );
    const bookedCount = bookedCountRow ? bookedCountRow.count : 0;

    if (cap < bookedCount) {
      return res.status(400).json({
        error: `Cannot reduce slot capacity below existing farmer bookings (${bookedCount} booked).`
      });
    }

    await runAsync(`UPDATE SLOTS SET max_capacity = ? WHERE id = ?`, [cap, id]);

    res.json({
      message: 'Slot capacity updated successfully',
      id: parseInt(id, 10),
      max_capacity: cap,
      booked_count: bookedCount,
      remaining_capacity: cap - bookedCount
    });
  } catch (err) {
    console.error('Update slot error:', err);
    res.status(500).json({ error: 'Error updating slot capacity.' });
  }
});

app.delete('/api/slots/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const bookedCountRow = await getAsync(
      `SELECT COUNT(*) as count FROM BOOKINGS WHERE slot_id = ? AND status != 'REJECTED'`,
      [id]
    );
    const bookedCount = bookedCountRow ? bookedCountRow.count : 0;

    if (bookedCount > 0) {
      return res.status(400).json({
        error: `Cannot delete slot with active farmer bookings (${bookedCount} booked).`
      });
    }

    await runAsync(`DELETE FROM SLOTS WHERE id = ?`, [id]);

    res.json({ message: 'Slot deleted successfully.' });
  } catch (err) {
    console.error('Delete slot error:', err);
    res.status(500).json({ error: 'Error deleting slot.' });
  }
});

// POST /api/slots/apply-schedule-range - Create schedule for date range skipping non-operational & holiday dates
app.post('/api/slots/apply-schedule-range', async (req, res) => {
  try {
    const { centre_id, max_quintals_per_day, time_slots } = req.body;
    const from_date = req.body.from_date || req.body.start_date;
    const to_date = req.body.to_date || req.body.end_date;

    if (!centre_id || !from_date || !to_date || !time_slots || !Array.isArray(time_slots) || time_slots.length === 0) {
      return res.status(400).json({ error: 'centre_id, from_date/start_date, to_date/end_date, and time_slots array are required.' });
    }

    const maxQ = parseFloat(max_quintals_per_day) || 500;

    // Fetch operational config
    const centre = await getAsync(`SELECT operating_days FROM PROCUREMENT_CENTRES WHERE centre_id = ?`, [centre_id]);
    let opDaysStr = centre && centre.operating_days ? centre.operating_days : 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday';
    if (opDaysStr === '[object Object]') {
      opDaysStr = 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday';
    }
    const allowedDays = opDaysStr.split(',').map(d => d.trim().toLowerCase());

    const exceptions = await allAsync(`SELECT date, reason FROM NON_OPERATIONAL_DATES WHERE centre_id = ?`, [centre_id]);
    const exceptionMap = {};
    exceptions.forEach(e => { exceptionMap[e.date] = e.reason || 'Non-operational date'; });

    let createdCount = 0;
    const skippedDates = [];

    let curr = new Date(from_date);
    const end = new Date(to_date);

    while (curr <= end) {
      const dateStr = curr.toISOString().split('T')[0];
      const dayName = getDayName(dateStr);

      // Check 1: Non-operational weekday
      if (!allowedDays.includes(dayName.toLowerCase())) {
        skippedDates.push({ date: dateStr, reason: `Non-operational day (${dayName})` });
        curr.setDate(curr.getDate() + 1);
        continue;
      }

      // Check 2: Holiday Exception
      if (exceptionMap[dateStr]) {
        skippedDates.push({ date: dateStr, reason: `Holiday exception (${exceptionMap[dateStr]})` });
        curr.setDate(curr.getDate() + 1);
        continue;
      }

      // Operational date -> Upsert Daily Capacity & Create Independent Slots
      await runAsync(
        `INSERT OR REPLACE INTO DAILY_CAPACITY (centre_id, date, max_quintals_per_day) VALUES (?, ?, ?)`,
        [centre_id, dateStr, maxQ]
      );

      for (const slot of time_slots) {
        const existing = await getAsync(
          `SELECT id FROM SLOTS WHERE centre_id = ? AND date = ? AND start_time = ? AND end_time = ?`,
          [centre_id, dateStr, slot.start_time, slot.end_time]
        );

        if (!existing) {
          await runAsync(
            `INSERT INTO SLOTS (centre_id, date, start_time, end_time, max_capacity) VALUES (?, ?, ?, ?, ?)`,
            [centre_id, dateStr, slot.start_time, slot.end_time, slot.max_capacity]
          );
        }
      }

      createdCount++;
      curr.setDate(curr.getDate() + 1);
    }

    res.json({
      message: `Schedule applied to ${createdCount} operational dates. Skipped ${skippedDates.length} non-operational dates.`,
      created_dates_count: createdCount,
      skipped_dates_count: skippedDates.length,
      skipped_dates: skippedDates
    });
  } catch (err) {
    console.error('Apply schedule range error:', err);
    res.status(500).json({ error: 'Error applying schedule range.' });
  }
});


// ----------------------------------------------------
// 5. BOOKINGS / APPOINTMENTS & CAPACITY VALIDATION
// ----------------------------------------------------

app.post('/api/bookings', async (req, res) => {
  try {
    const { farmer_id, centre_id, slot_id, crop, quantity } = req.body;

    if (!farmer_id || !centre_id || !slot_id || !crop || !quantity) {
      return res.status(400).json({ error: 'Farmer ID, Centre ID, Slot, Crop, and Quantity are required.' });
    }

    const qty = parseFloat(quantity);
    if (isNaN(qty) || qty <= 0) {
      return res.status(400).json({ error: 'Please enter a valid quantity in Quintals.' });
    }

    // 1. Verify Slot Existence & Date
    const slot = await getAsync(`SELECT * FROM SLOTS WHERE id = ?`, [slot_id]);
    if (!slot) {
      return res.status(404).json({ error: 'Selected time slot does not exist.' });
    }

    const dateStr = slot.date;
    const dayName = getDayName(dateStr);

    // 2. Validate Operational Days & Holiday Exceptions
    const centre = await getAsync(`SELECT * FROM PROCUREMENT_CENTRES WHERE centre_id = ?`, [centre_id]);
    if (centre && centre.operating_days && centre.operating_days !== '[object Object]') {
      const allowedDays = centre.operating_days.split(',').map(d => d.trim().toLowerCase());
      if (!allowedDays.includes(dayName.toLowerCase())) {
        return res.status(400).json({ error: `${centre.centre_name} is closed on ${dayName}s.` });
      }
    }

    const holiday = await getAsync(`SELECT reason FROM NON_OPERATIONAL_DATES WHERE centre_id = ? AND date = ?`, [centre_id, dateStr]);
    if (holiday) {
      return res.status(400).json({ error: `Centre Closed on ${dateStr} (${holiday.reason}).` });
    }

    // 3. Strict Server-Side Slot Farmer Capacity Check
    const countRow = await getAsync(
      `SELECT COUNT(*) as count FROM BOOKINGS WHERE slot_id = ? AND status != 'REJECTED'`,
      [slot_id]
    );
    const bookedCount = countRow ? countRow.count : 0;

    if (bookedCount >= slot.max_capacity) {
      return res.status(400).json({ error: 'Sorry, this slot is now full.' });
    }

    // 4. Strict Server-Side Daily Quintal Capacity Check
    const capRow = await getAsync(`SELECT max_quintals_per_day FROM DAILY_CAPACITY WHERE centre_id = ? AND date = ?`, [centre_id, dateStr]);
    const max_quintals_per_day = capRow ? capRow.max_quintals_per_day : 500;

    const sumRow = await getAsync(
      `SELECT SUM(b.quantity) as total_quintals FROM BOOKINGS b
       JOIN SLOTS s ON b.slot_id = s.id
       WHERE b.centre_id = ? AND s.date = ? AND b.status != 'REJECTED'`,
      [centre_id, dateStr]
    );
    const booked_quintals = sumRow && sumRow.total_quintals ? sumRow.total_quintals : 0;
    const remaining_quintals = Math.max(0, max_quintals_per_day - booked_quintals);

    if (booked_quintals + qty > max_quintals_per_day) {
      return res.status(400).json({
        error: `Daily quantity limit reached. Only ${remaining_quintals} Quintals remain available for this date.`
      });
    }

    // 5. Check Crop Support for Centre
    if (centre && centre.supported_crops) {
      const supported = centre.supported_crops.split(',').map(c => c.trim().toLowerCase());
      if (!supported.includes(crop.trim().toLowerCase())) {
        return res.status(400).json({ error: `Crop '${crop}' is not supported by ${centre.centre_name}.` });
      }
    }

    // 6. Generate Unique Appointment ID & QR Token
    const appointment_id = await generateAppointmentId(slot.date);
    const qr_token = generateQrToken(appointment_id);

    // 7. Insert Booking
    await runAsync(
      `INSERT INTO BOOKINGS (appointment_id, booking_id, farmer_id, centre_id, slot_id, crop, quantity, status, qr_token) VALUES (?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?)`,
      [appointment_id, appointment_id, farmer_id, centre_id, slot_id, crop, qty, qr_token]
    );

    const farmerObj = await getAsync(`SELECT name, mobile FROM USERS WHERE user_id = ?`, [farmer_id]);

    const createdBooking = {
      appointment_id,
      booking_id: appointment_id,
      farmer_id,
      farmer_name: farmerObj ? farmerObj.name : farmer_id,
      farmer_mobile: farmerObj ? farmerObj.mobile : '',
      centre_id,
      centre_name: centre ? centre.centre_name : centre_id,
      location: centre ? centre.location : '',
      crop,
      quantity: qty,
      date: slot.date,
      start_time: slot.start_time,
      end_time: slot.end_time,
      time_slot: `${slot.start_time} - ${slot.end_time}`,
      status: 'CONFIRMED',
      qr_token,
      created_at: new Date().toISOString()
    };

    res.status(201).json({
      message: 'Appointment booked successfully!',
      booking: createdBooking
    });
  } catch (err) {
    console.error('Create booking error:', err);
    res.status(500).json({ error: 'Server error while booking appointment.' });
  }
});

// GET /api/bookings/farmer/:farmer_id
app.get('/api/bookings/farmer/:farmer_id', async (req, res) => {
  try {
    const { farmer_id } = req.params;

    const bookings = await allAsync(
      `SELECT b.*, s.date, s.start_time, s.end_time, pc.centre_name, pc.location, u.name as farmer_name, u.mobile as farmer_mobile
       FROM BOOKINGS b
       JOIN SLOTS s ON b.slot_id = s.id
       JOIN PROCUREMENT_CENTRES pc ON b.centre_id = pc.centre_id
       LEFT JOIN USERS u ON b.farmer_id = u.user_id
       WHERE b.farmer_id = ?
       ORDER BY b.id DESC`,
      [farmer_id]
    );

    const formatted = bookings.map(b => ({
      id: b.id,
      appointment_id: b.appointment_id || b.booking_id,
      booking_id: b.appointment_id || b.booking_id,
      farmer_id: b.farmer_id,
      farmer_name: b.farmer_name || b.farmer_id,
      farmer_mobile: b.farmer_mobile || '',
      centre_id: b.centre_id,
      centre_name: b.centre_name,
      location: b.location,
      crop: b.crop,
      quantity: b.quantity,
      date: b.date,
      start_time: b.start_time,
      end_time: b.end_time,
      time_slot: `${b.start_time} - ${b.end_time}`,
      status: b.status,
      qr_token: b.qr_token || `BA-QR-${b.appointment_id}`,
      verified_at: b.verified_at,
      created_at: b.created_at
    }));

    res.json(formatted);
  } catch (err) {
    console.error('Fetch farmer bookings error:', err);
    res.status(500).json({ error: 'Error fetching farmer appointments.' });
  }
});

// GET /api/bookings/centre/:centre_id
app.get('/api/bookings/centre/:centre_id', async (req, res) => {
  try {
    const { centre_id } = req.params;
    const { date } = req.query;

    let query = `SELECT b.*, s.date, s.start_time, s.end_time, pc.centre_name, pc.location, u.name as farmer_name, u.mobile as farmer_mobile
       FROM BOOKINGS b
       JOIN SLOTS s ON b.slot_id = s.id
       JOIN PROCUREMENT_CENTRES pc ON b.centre_id = pc.centre_id
       LEFT JOIN USERS u ON b.farmer_id = u.user_id
       WHERE b.centre_id = ?`;
    const params = [centre_id];

    if (date) {
      query += ` AND s.date = ?`;
      params.push(date);
    }

    query += ` ORDER BY b.id DESC`;

    const bookings = await allAsync(query, params);


    const formatted = bookings.map(b => ({
      id: b.id,
      appointment_id: b.appointment_id || b.booking_id,
      booking_id: b.appointment_id || b.booking_id,
      farmer_id: b.farmer_id,
      farmer_name: b.farmer_name || b.farmer_id,
      farmer_mobile: b.farmer_mobile || '',
      centre_id: b.centre_id,
      centre_name: b.centre_name,
      location: b.location,
      crop: b.crop,
      quantity: b.quantity,
      date: b.date,
      start_time: b.start_time,
      end_time: b.end_time,
      time_slot: `${b.start_time} - ${b.end_time}`,
      status: b.status,
      verification_status: b.status === 'VERIFIED' ? 'VERIFIED ✓' : 'NOT VERIFIED',
      qr_token: b.qr_token || `BA-QR-${b.appointment_id}`,
      verified_at: b.verified_at,
      created_at: b.created_at
    }));

    res.json(formatted);
  } catch (err) {
    console.error('Fetch centre bookings error:', err);
    res.status(500).json({ error: 'Error fetching centre appointments.' });
  }
});

// PUT /api/bookings/:id/status
app.put('/api/bookings/:id/status', async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    const validStatuses = ['CONFIRMED', 'REJECTED', 'ARRIVED', 'VERIFIED', 'EXPIRED'];
    if (!validStatuses.includes(status.toUpperCase())) {
      return res.status(400).json({ error: `Invalid status.` });
    }

    const booking = await getAsync(`SELECT * FROM BOOKINGS WHERE id = ? OR appointment_id = ? OR booking_id = ?`, [id, id, id]);
    if (!booking) {
      return res.status(404).json({ error: 'Appointment not found.' });
    }

    const newStatus = status.toUpperCase();
    let verifiedAt = booking.verified_at;
    if (newStatus === 'VERIFIED' && !verifiedAt) {
      verifiedAt = new Date().toISOString();
    }

    await runAsync(`UPDATE BOOKINGS SET status = ?, verified_at = ? WHERE id = ?`, [newStatus, verifiedAt, booking.id]);

    res.json({
      message: `Appointment status updated to ${newStatus}`,
      appointment_id: booking.appointment_id,
      status: newStatus
    });
  } catch (err) {
    console.error('Update booking status error:', err);
    res.status(500).json({ error: 'Error updating status.' });
  }
});

// ----------------------------------------------------
// 6. QR VERIFICATION BACKEND ENDPOINT
// ----------------------------------------------------

app.post('/api/appointments/verify', async (req, res) => {
  try {
    const { qr_token, centre_id } = req.body;

    if (!qr_token || !centre_id) {
      return res.status(400).json({
        success: false,
        code: 'INVALID_REQUEST',
        error: 'INVALID APPOINTMENT ✕',
        message: 'Entry Not Accepted'
      });
    }

    const cleanToken = qr_token.trim();

    const booking = await getAsync(
      `SELECT b.*, s.date, s.start_time, s.end_time, pc.centre_name, pc.location, u.name as farmer_name, u.mobile as farmer_mobile
       FROM BOOKINGS b
       JOIN SLOTS s ON b.slot_id = s.id
       JOIN PROCUREMENT_CENTRES pc ON b.centre_id = pc.centre_id
       LEFT JOIN USERS u ON b.farmer_id = u.user_id
       WHERE LOWER(b.qr_token) = LOWER(?) OR LOWER(b.appointment_id) = LOWER(?) OR LOWER(b.booking_id) = LOWER(?)`,
      [cleanToken, cleanToken, cleanToken]
    );

    if (!booking) {
      return res.status(400).json({
        success: false,
        code: 'INVALID_QR',
        error: 'INVALID APPOINTMENT ✕',
        message: 'Entry Not Accepted. Unrecognized QR code.'
      });
    }

    if (booking.centre_id !== centre_id) {
      return res.status(400).json({
        success: false,
        code: 'WRONG_CENTRE',
        error: 'WRONG PROCUREMENT CENTRE ✕',
        message: 'Appointment does not belong to this centre.'
      });
    }

    if (booking.status === 'VERIFIED') {
      return res.status(400).json({
        success: false,
        code: 'ALREADY_VERIFIED',
        error: 'ALREADY VERIFIED',
        message: 'Appointment has already been used.'
      });
    }

    const todayStr = new Date().toISOString().split('T')[0];
    if (booking.date < todayStr) {
      return res.status(400).json({
        success: false,
        code: 'EXPIRED',
        error: 'APPOINTMENT EXPIRED',
        message: 'Entry Not Accepted. Scheduled date has passed.'
      });
    }

    if (booking.status === 'REJECTED') {
      return res.status(400).json({
        success: false,
        code: 'REJECTED',
        error: 'APPOINTMENT REJECTED ✕',
        message: 'This appointment has been rejected by the centre.'
      });
    }

    const verifiedAt = new Date().toISOString();
    await runAsync(
      `UPDATE BOOKINGS SET status = 'VERIFIED', verified_at = ? WHERE id = ?`,
      [verifiedAt, booking.id]
    );

    const updatedBooking = {
      appointment_id: booking.appointment_id,
      farmer_id: booking.farmer_id,
      farmer_name: booking.farmer_name || booking.farmer_id,
      farmer_mobile: booking.farmer_mobile || '',
      centre_id: booking.centre_id,
      centre_name: booking.centre_name,
      location: booking.location,
      crop: booking.crop,
      quantity: booking.quantity,
      date: booking.date,
      start_time: booking.start_time,
      end_time: booking.end_time,
      time_slot: `${booking.start_time} - ${booking.end_time}`,
      status: 'VERIFIED',
      verified_at: verifiedAt
    };

    res.json({
      success: true,
      code: 'SUCCESS',
      title: 'APPOINTMENT FOUND ✓',
      message: 'Appointment verified successfully.',
      appointment: updatedBooking
    });
  } catch (err) {
    console.error('QR verification error:', err);
    res.status(500).json({
      success: false,
      code: 'SERVER_ERROR',
      error: 'INVALID APPOINTMENT ✕',
      message: 'Server error during QR verification.'
    });
  }
});

// ----------------------------------------------------
// 7. STATS API
// ----------------------------------------------------

app.get('/api/stats', async (req, res) => {
  try {
    const farmersCount = await getAsync(`SELECT COUNT(*) as count FROM USERS WHERE role = 'farmer'`);
    const centresCount = await getAsync(`SELECT COUNT(*) as count FROM PROCUREMENT_CENTRES`);
    const bookingsCount = await getAsync(`SELECT COUNT(*) as count FROM BOOKINGS`);

    res.json({
      farmers_registered: 2500 + (farmersCount ? farmersCount.count : 0),
      procurement_centres: 120 + (centresCount ? centresCount.count : 0),
      slots_managed: 5000 + (bookingsCount ? bookingsCount.count : 0)
    });
  } catch (err) {
    console.error('Stats error:', err);
    res.status(500).json({ error: 'Error fetching statistics.' });
  }
});

app.listen(PORT, () => {
  console.log(`BHARATAGRI Backend Server listening on http://localhost:${PORT}`);
});
