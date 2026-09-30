/**
 * Standardized Date Utility for BHARATAGRI
 * 
 * User-facing display format: DD-MM-YYYY (e.g., 12-09-2026)
 * Backend / database storage format: YYYY-MM-DD (e.g., 2026-09-12)
 */

/**
 * Format any date input (YYYY-MM-DD, ISO string, Date object, or DD-MM-YYYY)
 * to user-facing DD-MM-YYYY format.
 */
export function formatDateDisplay(dateInput) {
  if (!dateInput) return '';

  if (dateInput instanceof Date) {
    if (isNaN(dateInput.getTime())) return '';
    const day = String(dateInput.getDate()).padStart(2, '0');
    const month = String(dateInput.getMonth() + 1).padStart(2, '0');
    const year = dateInput.getFullYear();
    return `${day}-${month}-${year}`;
  }

  const str = String(dateInput).trim();

  // If already in DD-MM-YYYY format
  if (/^\d{2}-\d{2}-\d{4}$/.test(str)) {
    return str;
  }

  // Handle YYYY-MM-DD or ISO strings (e.g. 2026-09-15 or 2026-09-15T00:00:00)
  if (/^\d{4}-\d{2}-\d{2}/.test(str)) {
    const cleanStr = str.split('T')[0];
    const parts = cleanStr.split('-');
    if (parts.length === 3) {
      const year = parts[0];
      const month = parts[1].padStart(2, '0');
      const day = parts[2].padStart(2, '0');
      return `${day}-${month}-${year}`;
    }
  }

  // Fallback to JS Date object parsing for other strings
  const d = new Date(str);
  if (!isNaN(d.getTime())) {
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    return `${day}-${month}-${year}`;
  }

  return str;
}

/**
 * Parse a DD-MM-YYYY (or YYYY-MM-DD) string into backend machine-readable YYYY-MM-DD format.
 */
export function parseDisplayToIso(displayStr) {
  if (!displayStr) return '';
  const str = String(displayStr).trim();

  if (/^\d{4}-\d{2}-\d{2}$/.test(str)) {
    return str;
  }

  if (/^\d{2}-\d{2}-\d{4}$/.test(str)) {
    const [day, month, year] = str.split('-');
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
  }

  return str;
}

/**
 * Normalize any date input into YYYY-MM-DD ISO string format.
 */
export function toIsoDate(dateInput) {
  if (!dateInput) return '';

  if (dateInput instanceof Date) {
    if (isNaN(dateInput.getTime())) return '';
    const year = dateInput.getFullYear();
    const month = String(dateInput.getMonth() + 1).padStart(2, '0');
    const day = String(dateInput.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  return parseDisplayToIso(dateInput);
}

/**
 * Get today's date in YYYY-MM-DD format using local time.
 */
export function getTodayIso() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get today's date in DD-MM-YYYY format.
 */
export function getTodayDisplay() {
  return formatDateDisplay(getTodayIso());
}

/**
 * Check if day, month, year form a valid calendar date.
 */
export function isValidDate(day, month, year) {
  const d = parseInt(day, 10);
  const m = parseInt(month, 10);
  const y = parseInt(year, 10);

  if (isNaN(d) || isNaN(m) || isNaN(y)) return false;
  if (y < 1900 || y > 2100) return false;
  if (m < 1 || m > 12) return false;

  const daysInMonth = new Date(y, m, 0).getDate();
  return d >= 1 && d <= daysInMonth;
}

/**
 * Validate DD-MM-YYYY format string.
 */
export function isValidDisplayDate(displayStr) {
  if (!displayStr || !/^\d{2}-\d{2}-\d{4}$/.test(displayStr.trim())) return false;
  const [day, month, year] = displayStr.trim().split('-');
  return isValidDate(day, month, year);
}

/**
 * Add N days to a date string or Date object, returning YYYY-MM-DD.
 */
export function addDays(dateInput, daysToAdd) {
  const iso = toIsoDate(dateInput);
  if (!iso) return '';
  const [y, m, d] = iso.split('-').map(Number);
  const dateObj = new Date(y, m - 1, d);
  dateObj.setDate(dateObj.getDate() + Number(daysToAdd));
  return toIsoDate(dateObj);
}

/**
 * Compare two dates. Returns negative if d1 < d2, 0 if d1 === d2, positive if d1 > d2.
 */
export function compareDates(d1, d2) {
  const iso1 = toIsoDate(d1);
  const iso2 = toIsoDate(d2);
  if (!iso1 || !iso2) return 0;
  return iso1.localeCompare(iso2);
}

export function isDateBefore(d1, d2) {
  return compareDates(d1, d2) < 0;
}

export function isDateAfter(d1, d2) {
  return compareDates(d1, d2) > 0;
}

export function isSameDate(d1, d2) {
  return compareDates(d1, d2) === 0;
}
