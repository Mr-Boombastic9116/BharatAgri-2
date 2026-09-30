const { initDatabase, runAsync, getAsync } = require('./db');

async function seedData() {
  await initDatabase();

  await runAsync(`DELETE FROM BOOKINGS`);
  await runAsync(`DELETE FROM SLOTS`);
  await runAsync(`DELETE FROM DAILY_CAPACITY`);
  await runAsync(`DELETE FROM NON_OPERATIONAL_DATES`);
  await runAsync(`DELETE FROM PROCUREMENT_CENTRES`);
  await runAsync(`DELETE FROM USERS`);

  console.log('Seeding BHARATAGRI dataset with operational days, holidays & daily capacity limits...');

  // 1. Seed Procurement Centres
  const centres = [
    {
      centre_name: 'XYZ Procurement Centre',
      centre_id: 'CENTRE-001',
      password: 'pass123',
      location: 'Ponda, Goa',
      contact_number: '9876543210',
      operating_days: 'Monday,Tuesday,Wednesday,Thursday,Friday,Saturday',
      opening_time: '09:00 AM',
      closing_time: '05:00 PM',
      supported_crops: 'Paddy,Wheat,Maize,Cotton'
    },
    {
      centre_name: 'ABC Procurement Centre',
      centre_id: 'CENTRE-002',
      password: 'pass123',
      location: 'Margao, Goa',
      contact_number: '9876543211',
      operating_days: 'Monday,Tuesday,Wednesday,Thursday,Friday',
      opening_time: '08:30 AM',
      closing_time: '04:30 PM',
      supported_crops: 'Paddy,Wheat,Soybean'
    },
    {
      centre_name: 'Shivaji Nagar Procurement Centre',
      centre_id: 'CENTRE-003',
      password: 'pass123',
      location: 'Mapusa, Goa',
      contact_number: '9876543212',
      operating_days: 'Tuesday,Wednesday,Thursday,Friday,Saturday',
      opening_time: '09:00 AM',
      closing_time: '05:00 PM',
      supported_crops: 'Wheat,Maize,Soybean,Cotton'
    }
  ];

  for (const c of centres) {
    await runAsync(
      `INSERT INTO PROCUREMENT_CENTRES (centre_name, centre_id, location, contact_number, operating_days, opening_time, closing_time, supported_crops)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [c.centre_name, c.centre_id, c.location, c.contact_number, c.operating_days, c.opening_time, c.closing_time, c.supported_crops]
    );

    await runAsync(
      `INSERT INTO USERS (name, user_id, password, role) VALUES (?, ?, ?, 'centre')`,
      [c.centre_name, c.centre_id, c.password]
    );
  }

  // 2. Seed Non-Operational Dates Exceptions
  await runAsync(
    `INSERT INTO NON_OPERATIONAL_DATES (centre_id, date, reason) VALUES (?, ?, ?)`,
    ['CENTRE-001', '2026-09-17', 'Public Holiday — Ganesh Chaturthi']
  );

  // 3. Seed Farmers
  const farmers = [
    { name: 'Ramesh Kumar', mobile: '9823012345', village: 'Ponda', user_id: 'FARMER-101', password: 'pass123', preferred_language: 'Hindi' },
    { name: 'Suresh Patel', mobile: '9823012346', village: 'Margao', user_id: 'FARMER-102', password: 'pass123', preferred_language: 'Marathi' },
    { name: 'Anita Singh', mobile: '9823012347', village: 'Mapusa', user_id: 'FARMER-103', password: 'pass123', preferred_language: 'English' },
    { name: 'Rajesh Sharma', mobile: '9823012348', village: 'Panaji', user_id: 'FARMER-104', password: 'pass123', preferred_language: 'Hindi' },
    { name: 'Priya Verma', mobile: '9823012349', village: 'Bicholim', user_id: 'FARMER-105', password: 'pass123', preferred_language: 'Konkani' }
  ];

  for (const f of farmers) {
    await runAsync(
      `INSERT INTO USERS (name, mobile, village, user_id, password, preferred_language, role) VALUES (?, ?, ?, ?, ?, ?, 'farmer')`,
      [f.name, f.mobile, f.village, f.user_id, f.password, f.preferred_language]
    );
  }

  // 4. Seed Slots & Daily Capacity
  const today = new Date().toISOString().split('T')[0];
  const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
  const dayAfter = new Date(Date.now() + 172800000).toISOString().split('T')[0];
  const sep15 = '2026-09-15';

  const timeSlots = [
    { start_time: '09:00 AM', end_time: '10:00 AM', max_capacity: 20 },
    { start_time: '10:00 AM', end_time: '11:00 AM', max_capacity: 20 },
    { start_time: '11:00 AM', end_time: '12:00 PM', max_capacity: 15 },
    { start_time: '12:00 PM', end_time: '01:00 PM', max_capacity: 15 },
    { start_time: '02:00 PM', end_time: '03:00 PM', max_capacity: 10 }
  ];

  const datesToSeed = [today, tomorrow, dayAfter, sep15];

  for (const c of centres) {
    for (const d of datesToSeed) {
      // Set Daily Capacity (500 Quintals)
      await runAsync(
        `INSERT INTO DAILY_CAPACITY (centre_id, date, max_quintals_per_day) VALUES (?, ?, ?)`,
        [c.centre_id, d, 500]
      );

      for (let i = 0; i < timeSlots.length; i++) {
        const slot = timeSlots[i];
        const cap = (i === 1 && c.centre_id === 'CENTRE-001') ? 2 : slot.max_capacity;
        await runAsync(
          `INSERT INTO SLOTS (centre_id, date, start_time, end_time, max_capacity) VALUES (?, ?, ?, ?, ?)`,
          [c.centre_id, d, slot.start_time, slot.end_time, cap]
        );
      }
    }
  }

  // 5. Seed Appointments / Bookings
  const slot1 = await getAsync(`SELECT id FROM SLOTS WHERE centre_id = 'CENTRE-001' AND start_time = '09:00 AM' LIMIT 1`);
  const slot2 = await getAsync(`SELECT id FROM SLOTS WHERE centre_id = 'CENTRE-001' AND start_time = '10:00 AM' LIMIT 1`);
  const slot3 = await getAsync(`SELECT id FROM SLOTS WHERE centre_id = 'CENTRE-002' AND start_time = '09:00 AM' LIMIT 1`);

  if (slot1) {
    await runAsync(
      `INSERT INTO BOOKINGS (appointment_id, booking_id, farmer_id, centre_id, slot_id, crop, quantity, status, qr_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      ['PF-260915-001', 'PF-260915-001', 'FARMER-101', 'CENTRE-001', slot1.id, 'Paddy', 250, 'CONFIRMED', 'BA-QR-PF-260915-001']
    );
  }

  if (slot2) {
    await runAsync(
      `INSERT INTO BOOKINGS (appointment_id, booking_id, farmer_id, centre_id, slot_id, crop, quantity, status, qr_token) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      ['PF-260915-002', 'PF-260915-002', 'FARMER-102', 'CENTRE-001', slot2.id, 'Wheat', 150, 'ARRIVED', 'BA-QR-PF-260915-002']
    );
  }

  if (slot3) {
    await runAsync(
      `INSERT INTO BOOKINGS (appointment_id, booking_id, farmer_id, centre_id, slot_id, crop, quantity, status, qr_token, verified_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`,
      ['PF-260915-003', 'PF-260915-003', 'FARMER-103', 'CENTRE-002', slot3.id, 'Soybean', 100, 'VERIFIED', 'BA-QR-PF-260915-003']
    );
  }

  console.log('Dataset seeded successfully with daily quintals & holidays!');
}

if (require.main === module) {
  seedData()
    .then(() => process.exit(0))
    .catch((err) => {
      console.error('Seed error:', err);
      process.exit(1);
    });
}

module.exports = seedData;
