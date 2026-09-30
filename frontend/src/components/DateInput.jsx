import React, { useState, useEffect, useRef } from 'react';
import { Calendar, ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { 
  formatDateDisplay, 
  parseDisplayToIso, 
  toIsoDate, 
  isValidDisplayDate,
  getTodayIso
} from '../utils/dateUtils';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const WEEKDAY_NAMES = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

/**
 * Standardized DateInput Component
 * 
 * Enforces DD-MM-YYYY user display across all browsers and locales,
 * while transparently providing YYYY-MM-DD ISO date to the parent onChange.
 * 
 * Props:
 * - value: string (YYYY-MM-DD or DD-MM-YYYY)
 * - onChange: function(isoDateString)
 * - min: string (YYYY-MM-DD or DD-MM-YYYY)
 * - max: string (YYYY-MM-DD or DD-MM-YYYY)
 * - disabled: boolean
 * - required: boolean
 * - placeholder: string (defaults to "DD-MM-YYYY")
 * - className: string
 * - style: object
 * - id: string
 */
export default function DateInput({
  value,
  onChange,
  min,
  max,
  disabled = false,
  required = false,
  placeholder = 'DD-MM-YYYY',
  className = '',
  style = {},
  id
}) {
  const [displayText, setDisplayText] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  // Parse initial calendar view month & year based on value or today
  const isoCurrent = toIsoDate(value) || getTodayIso();
  const [currentYear, setCurrentYear] = useState(() => {
    const parts = isoCurrent.split('-');
    return parseInt(parts[0], 10) || new Date().getFullYear();
  });
  const [currentMonth, setCurrentMonth] = useState(() => {
    const parts = isoCurrent.split('-');
    return (parseInt(parts[1], 10) - 1) || new Date().getMonth();
  });

  // Sync display text when value prop changes from parent
  useEffect(() => {
    if (value) {
      setDisplayText(formatDateDisplay(value));
      const iso = toIsoDate(value);
      if (iso) {
        const [y, m] = iso.split('-').map(Number);
        setCurrentYear(y);
        setCurrentMonth(m - 1);
      }
    } else {
      setDisplayText('');
    }
  }, [value]);

  // Handle outside click to close calendar popup
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Handle manual typing with auto-masking for DD-MM-YYYY
  const handleInputChange = (e) => {
    let inputVal = e.target.value;

    // Filter out any character that is not a digit or hyphen
    inputVal = inputVal.replace(/[^\d-]/g, '');

    // Auto-insert hyphens if user is typing pure digits
    const digits = inputVal.replace(/-/g, '');
    let formatted = '';
    if (digits.length > 0) {
      formatted = digits.substring(0, 2);
      if (digits.length >= 3) {
        formatted += '-' + digits.substring(2, 4);
      }
      if (digits.length >= 5) {
        formatted += '-' + digits.substring(4, 8);
      }
    } else {
      formatted = inputVal;
    }

    setDisplayText(formatted);

    // If a complete 10-character DD-MM-YYYY is entered, validate and trigger onChange
    if (formatted.length === 10) {
      if (isValidDisplayDate(formatted)) {
        const iso = parseDisplayToIso(formatted);
        if (isDateAllowed(iso)) {
          onChange(iso);
        }
      }
    } else if (formatted === '' && !required) {
      onChange('');
    }
  };

  const handleInputBlur = () => {
    if (!displayText) {
      if (required && value) {
        setDisplayText(formatDateDisplay(value));
      }
      return;
    }

    if (isValidDisplayDate(displayText)) {
      const iso = parseDisplayToIso(displayText);
      if (isDateAllowed(iso)) {
        onChange(iso);
        return;
      }
    }

    // Revert to current valid value if typed input is invalid
    if (value) {
      setDisplayText(formatDateDisplay(value));
    } else {
      setDisplayText('');
    }
  };

  const isDateAllowed = (isoDate) => {
    if (!isoDate) return false;
    const minIso = min ? toIsoDate(min) : null;
    const maxIso = max ? toIsoDate(max) : null;

    if (minIso && isoDate < minIso) return false;
    if (maxIso && isoDate > maxIso) return false;
    return true;
  };

  const handleSelectDay = (day) => {
    const mm = String(currentMonth + 1).padStart(2, '0');
    const dd = String(day).padStart(2, '0');
    const iso = `${currentYear}-${mm}-${dd}`;

    if (!isDateAllowed(iso)) return;

    onChange(iso);
    setDisplayText(`${dd}-${mm}-${currentYear}`);
    setIsOpen(false);
  };

  const handlePrevMonth = (e) => {
    e.stopPropagation();
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(y => y - 1);
    } else {
      setCurrentMonth(m => m - 1);
    }
  };

  const handleNextMonth = (e) => {
    e.stopPropagation();
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(y => y + 1);
    } else {
      setCurrentMonth(m => m + 1);
    }
  };

  const handleSelectToday = (e) => {
    e.stopPropagation();
    const todayIso = getTodayIso();
    if (isDateAllowed(todayIso)) {
      onChange(todayIso);
      setDisplayText(formatDateDisplay(todayIso));
      const [y, m] = todayIso.split('-').map(Number);
      setCurrentYear(y);
      setCurrentMonth(m - 1);
      setIsOpen(false);
    }
  };

  // Compute days in current month and first weekday (Monday as 0)
  const daysInCurrentMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDaySundayBased = new Date(currentYear, currentMonth, 1).getDay(); // 0 = Sun
  const firstDayMondayBased = (firstDaySundayBased + 6) % 7; // 0 = Mon, 6 = Sun

  const selectedIso = toIsoDate(value);
  const selectedDay = selectedIso && selectedIso.startsWith(`${currentYear}-${String(currentMonth + 1).padStart(2, '0')}`)
    ? parseInt(selectedIso.split('-')[2], 10)
    : null;

  return (
    <div 
      ref={containerRef} 
      style={{ position: 'relative', display: 'inline-block', width: '100%', ...style }}
      className={`date-input-container ${className}`}
    >
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          id={id}
          type="text"
          className="form-control"
          placeholder={placeholder}
          value={displayText}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          disabled={disabled}
          required={required}
          maxLength={10}
          style={{
            paddingRight: '38px',
            fontFamily: 'monospace',
            fontWeight: 600,
            letterSpacing: '0.5px'
          }}
        />

        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          title="Open Calendar (DD-MM-YYYY)"
          style={{
            position: 'absolute',
            right: '8px',
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'none',
            border: 'none',
            cursor: disabled ? 'not-allowed' : 'pointer',
            color: isOpen ? 'var(--primary)' : 'var(--muted)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '4px',
            borderRadius: '4px',
            transition: 'color 0.2s'
          }}
        >
          <Calendar size={18} />
        </button>
      </div>

      {/* Interactive Calendar Dropdown */}
      {isOpen && !disabled && (
        <div 
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            zIndex: 1100,
            backgroundColor: '#ffffff',
            borderRadius: '10px',
            border: '1px solid var(--border, #cbd5e1)',
            boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            padding: '14px',
            width: '280px',
            userSelect: 'none'
          }}
        >
          {/* Calendar Header: Month/Year navigation */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <button
              type="button"
              onClick={handlePrevMonth}
              className="btn btn-outline btn-sm"
              style={{ padding: '4px 8px', borderRadius: '6px' }}
              title="Previous Month"
            >
              <ChevronLeft size={16} />
            </button>

            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--secondary, #1e293b)' }}>
              {MONTH_NAMES[currentMonth]} {currentYear}
            </span>

            <button
              type="button"
              onClick={handleNextMonth}
              className="btn btn-outline btn-sm"
              style={{ padding: '4px 8px', borderRadius: '6px' }}
              title="Next Month"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          {/* Weekday Labels (Mon - Sun) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '2px', textAlign: 'center', marginBottom: '6px' }}>
            {WEEKDAY_NAMES.map(day => (
              <span key={day} style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--muted, #64748b)' }}>
                {day}
              </span>
            ))}
          </div>

          {/* Day Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', textAlign: 'center' }}>
            {/* Empty slots before first day */}
            {Array.from({ length: firstDayMondayBased }).map((_, idx) => (
              <div key={`empty-${idx}`} style={{ height: '32px' }} />
            ))}

            {/* Days in Month */}
            {Array.from({ length: daysInCurrentMonth }).map((_, idx) => {
              const day = idx + 1;
              const mm = String(currentMonth + 1).padStart(2, '0');
              const dd = String(day).padStart(2, '0');
              const iso = `${currentYear}-${mm}-${dd}`;
              const isSelected = selectedDay === day;
              const isAllowed = isDateAllowed(iso);
              const isToday = iso === getTodayIso();

              return (
                <button
                  key={day}
                  type="button"
                  onClick={() => isAllowed && handleSelectDay(day)}
                  disabled={!isAllowed}
                  style={{
                    height: '32px',
                    width: '32px',
                    margin: '0 auto',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.85rem',
                    fontWeight: isSelected || isToday ? 700 : 500,
                    borderRadius: '6px',
                    border: isToday && !isSelected ? '1.5px solid var(--primary, #16a34a)' : 'none',
                    backgroundColor: isSelected 
                      ? 'var(--primary, #16a34a)' 
                      : 'transparent',
                    color: isSelected 
                      ? '#ffffff' 
                      : !isAllowed 
                        ? '#cbd5e1' 
                        : isToday 
                          ? 'var(--primary, #16a34a)' 
                          : 'var(--secondary, #1e293b)',
                    cursor: isAllowed ? 'pointer' : 'not-allowed',
                    transition: 'all 0.15s'
                  }}
                  onMouseEnter={(e) => {
                    if (isAllowed && !isSelected) {
                      e.currentTarget.style.backgroundColor = '#f1f5f9';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (isAllowed && !isSelected) {
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  {day}
                </button>
              );
            })}
          </div>

          {/* Calendar Footer: Today button & DD-MM-YYYY badge */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '8px', borderTop: '1px solid #f1f5f9' }}>
            <button
              type="button"
              onClick={handleSelectToday}
              className="btn btn-outline btn-sm"
              style={{ fontSize: '0.75rem', padding: '2px 8px' }}
            >
              Today
            </button>

            <span style={{ fontSize: '0.75rem', color: 'var(--muted, #64748b)', fontWeight: 600 }}>
              Format: DD-MM-YYYY
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
