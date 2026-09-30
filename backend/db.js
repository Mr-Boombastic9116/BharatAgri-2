const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'bharatagri.db');

const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error connecting to SQLite database:', err.message);
  } else {
    console.log('Connected to SQLite database at:', dbPath);
  }
});

function runAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve(this);
    });
  });
}

function getAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

function allAsync(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

async function initDatabase() {
  await runAsync(`
    CREATE TABLE IF NOT EXISTS USERS (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      mobile TEXT,
      village TEXT,
      user_id TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      preferred_language TEXT DEFAULT 'English',
      role TEXT NOT NULL CHECK(role IN ('farmer', 'centre'))
    );
  `);

  await runAsync(`
    CREATE TABLE IF NOT EXISTS PROCUREMENT_CENTRES (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      centre_name TEXT NOT NULL,
      centre_id TEXT UNIQUE NOT NULL,
      location TEXT,
      contact_number TEXT,
      operating_days TEXT,
      opening_time TEXT DEFAULT '09:00 AM',
      closing_time TEXT DEFAULT '05:00 PM',
      supported_crops TEXT
    );
  `);

  await runAsync(`
    CREATE TABLE IF NOT EXISTS NON_OPERATIONAL_DATES (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      centre_id TEXT NOT NULL,
      date TEXT NOT NULL,
      reason TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(centre_id, date)
    );
  `);

  await runAsync(`
    CREATE TABLE IF NOT EXISTS DAILY_CAPACITY (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      centre_id TEXT NOT NULL,
      date TEXT NOT NULL,
      max_quintals_per_day REAL NOT NULL DEFAULT 500,
      UNIQUE(centre_id, date)
    );
  `);

  await runAsync(`
    CREATE TABLE IF NOT EXISTS SLOTS (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      centre_id TEXT NOT NULL,
      date TEXT NOT NULL,
      start_time TEXT NOT NULL,
      end_time TEXT NOT NULL,
      max_capacity INTEGER NOT NULL DEFAULT 20
    );
  `);

  await runAsync(`
    CREATE TABLE IF NOT EXISTS BOOKINGS (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      appointment_id TEXT UNIQUE NOT NULL,
      booking_id TEXT,
      farmer_id TEXT NOT NULL,
      centre_id TEXT NOT NULL,
      slot_id INTEGER NOT NULL,
      crop TEXT NOT NULL,
      quantity REAL NOT NULL,
      status TEXT NOT NULL DEFAULT 'CONFIRMED',
      qr_token TEXT UNIQUE NOT NULL,
      verified_at DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (slot_id) REFERENCES SLOTS(id)
    );
  `);

  console.log('Database schema created cleanly with hierarchy & daily capacity support.');
}

module.exports = {
  db,
  runAsync,
  getAsync,
  allAsync,
  initDatabase
};
