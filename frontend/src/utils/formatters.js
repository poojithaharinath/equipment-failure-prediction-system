/**
 * formatters.js
 * Shared utility functions for formatting dates, numbers, durations,
 * sensor values, risk levels and status labels across all pages.
 */

// ---------------------------------------------------------------------------
// Date & Time
// ---------------------------------------------------------------------------

/**
 * Format an ISO timestamp to a human-readable local date+time string.
 * @param {string|Date} ts
 * @param {boolean} includeTime
 * @returns {string}
 */
export function formatTimestamp(ts, includeTime = true) {
  if (!ts) return '—';
  const d = new Date(ts);
  if (isNaN(d)) return String(ts);
  const dateStr = d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  if (!includeTime) return dateStr;
  const timeStr = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  return `${dateStr}, ${timeStr}`;
}

/**
 * Format a date only (no time component).
 * @param {string|Date} ts
 * @returns {string}
 */
export function formatDate(ts) {
  return formatTimestamp(ts, false);
}

/**
 * Format a duration given in minutes to a human-readable string.
 * e.g. 150 → "2h 30m"
 * @param {number} minutes
 * @returns {string}
 */
export function formatDuration(minutes) {
  if (minutes == null || isNaN(minutes)) return '—';
  const mins = Math.round(Number(minutes));
  if (mins < 60) return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return m === 0 ? `${h}h` : `${h}h ${m}m`;
}

/**
 * Format hours to a human-readable string.
 * e.g. 2.5 → "2h 30m"
 * @param {number} hours
 * @returns {string}
 */
export function formatHours(hours) {
  if (hours == null || isNaN(hours)) return '—';
  return formatDuration(Math.round(Number(hours) * 60));
}

/**
 * Returns a relative time string such as "3 days ago", "just now".
 * @param {string|Date} ts
 * @returns {string}
 */
export function timeAgo(ts) {
  if (!ts) return '—';
  const diff = Date.now() - new Date(ts).getTime();
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

// ---------------------------------------------------------------------------
// Numbers & Percentages
// ---------------------------------------------------------------------------

/**
 * Format a floating-point number to a fixed number of decimal places.
 * @param {number} value
 * @param {number} decimals
 * @returns {string}
 */
export function formatNumber(value, decimals = 1) {
  if (value == null || isNaN(value)) return '—';
  return Number(value).toFixed(decimals);
}

/**
 * Format a probability (0–1) or score as a percentage string.
 * e.g. 0.9372 → "93.7%"
 * @param {number} value  value between 0 and 1
 * @param {number} decimals
 * @returns {string}
 */
export function formatProbability(value, decimals = 1) {
  if (value == null || isNaN(value)) return '—';
  return `${(Number(value) * 100).toFixed(decimals)}%`;
}

/**
 * Format a percentage value that is already in 0–100 range.
 * e.g. 93.72 → "93.7%"
 * @param {number} value  value between 0 and 100
 * @param {number} decimals
 * @returns {string}
 */
export function formatPercent(value, decimals = 1) {
  if (value == null || isNaN(value)) return '—';
  return `${Number(value).toFixed(decimals)}%`;
}

/**
 * Format a currency value.
 * e.g. 1234.5 → "$1,234.50"
 * @param {number} value
 * @param {string} currency
 * @returns {string}
 */
export function formatCurrency(value, currency = 'USD') {
  if (value == null || isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

/**
 * Format a large integer with locale-appropriate thousands separators.
 * e.g. 1250000 → "1,250,000"
 * @param {number} value
 * @returns {string}
 */
export function formatCount(value) {
  if (value == null || isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US').format(Number(value));
}

// ---------------------------------------------------------------------------
// Sensor Values
// ---------------------------------------------------------------------------

/** Units for each sensor type. */
const SENSOR_UNITS = {
  TEMPERATURE: '°C',
  VIBRATION: 'mm/s',
  PRESSURE: 'Bar',
  CURRENT: 'A',
  RPM: 'RPM',
};

/**
 * Format a raw sensor reading with its unit.
 * @param {number} value
 * @param {string} sensorType  e.g. "TEMPERATURE"
 * @param {number} decimals
 * @returns {string}
 */
export function formatSensorValue(value, sensorType, decimals = 2) {
  if (value == null || isNaN(value)) return '—';
  const unit = SENSOR_UNITS[sensorType] || '';
  return `${Number(value).toFixed(decimals)}${unit ? ' ' + unit : ''}`;
}

// ---------------------------------------------------------------------------
// Risk & Status Labels
// ---------------------------------------------------------------------------

/**
 * Returns Tailwind CSS classes for a given risk category badge.
 * @param {string} riskCategory  "High Risk" | "Medium Risk" | "Low Risk"
 * @returns {{ bg: string, text: string, border: string }}
 */
export function getRiskClasses(riskCategory) {
  switch (riskCategory) {
    case 'High Risk':
      return { bg: 'bg-rose-500/20', text: 'text-rose-400', border: 'border-rose-700' };
    case 'Medium Risk':
      return { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-700' };
    case 'Low Risk':
    default:
      return { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-700' };
  }
}

/**
 * Returns Tailwind CSS classes for a machine/work-order status badge.
 * @param {string} status
 * @returns {{ bg: string, text: string }}
 */
export function getStatusClasses(status) {
  switch (status) {
    case 'OPERATIONAL':
    case 'COMPLETED':
    case 'ACTIVE':
    case 'AVAILABLE':
      return { bg: 'bg-emerald-500/20', text: 'text-emerald-400' };
    case 'DEGRADED':
    case 'IN_PROGRESS':
    case 'CALIBRATING':
      return { bg: 'bg-amber-500/20', text: 'text-amber-400' };
    case 'FAILED':
    case 'FAULTY':
    case 'CANCELLED':
      return { bg: 'bg-rose-500/20', text: 'text-rose-400' };
    case 'MAINTENANCE':
    case 'OFFLINE':
    case 'PENDING':
    case 'ON_LEAVE':
      return { bg: 'bg-slate-500/20', text: 'text-slate-400' };
    default:
      return { bg: 'bg-blue-500/20', text: 'text-blue-400' };
  }
}

/**
 * Returns Tailwind CSS classes for a severity badge.
 * @param {string} severity  "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
 * @returns {{ bg: string, text: string }}
 */
export function getSeverityClasses(severity) {
  switch (severity) {
    case 'CRITICAL':
    case 'SEVERE':
      return { bg: 'bg-rose-500/20', text: 'text-rose-400' };
    case 'HIGH':
    case 'MODERATE':
      return { bg: 'bg-amber-500/20', text: 'text-amber-400' };
    case 'MEDIUM':
      return { bg: 'bg-yellow-500/20', text: 'text-yellow-400' };
    case 'LOW':
    default:
      return { bg: 'bg-blue-500/20', text: 'text-blue-400' };
  }
}

/**
 * Map a failure_probability_pct (0–100) to a colour for progress bars.
 * @param {number} pct
 * @returns {string} Tailwind background class
 */
export function getProbabilityBarColor(pct) {
  if (pct > 70) return 'bg-rose-500';
  if (pct > 35) return 'bg-amber-500';
  return 'bg-emerald-500';
}

// ---------------------------------------------------------------------------
// String Helpers
// ---------------------------------------------------------------------------

/**
 * Convert an UPPER_SNAKE_CASE string to Title Case With Spaces.
 * e.g. "BEARING_WEAR" → "Bearing Wear"
 * @param {string} str
 * @returns {string}
 */
export function snakeToTitle(str) {
  if (!str) return '';
  return str
    .toLowerCase()
    .split('_')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/**
 * Truncate a string to a maximum length, appending ellipsis if needed.
 * @param {string} str
 * @param {number} maxLen
 * @returns {string}
 */
export function truncate(str, maxLen = 60) {
  if (!str) return '';
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}

