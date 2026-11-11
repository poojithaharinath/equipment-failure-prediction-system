/**
 * StatusBadge.jsx
 * Reusable badge for Machine/Sensor status, severity, resolution status,
 * and ML risk category labels. Used across all 9 dashboard pages.
 *
 * Usage:
 *   <StatusBadge type="status" value="OPERATIONAL" />
 *   <StatusBadge type="risk"   value="High Risk"   />
 *   <StatusBadge type="severity" value="CRITICAL"  />
 *   <StatusBadge type="resolution" value="UNRESOLVED" size="sm" />
 */

import React from 'react';

// ---------------------------------------------------------------------------
// Colour maps — Tailwind classes, keyed by value
// ---------------------------------------------------------------------------

const STATUS_CLASSES = {
  OPERATIONAL:  'bg-emerald-500/20 text-emerald-400',
  ACTIVE:       'bg-emerald-500/20 text-emerald-400',
  AVAILABLE:    'bg-emerald-500/20 text-emerald-400',
  COMPLETED:    'bg-emerald-500/20 text-emerald-400',
  DEGRADED:     'bg-amber-500/20 text-amber-400',
  IN_PROGRESS:  'bg-amber-500/20 text-amber-400',
  CALIBRATING:  'bg-amber-500/20 text-amber-400',
  ASSIGNED:     'bg-amber-500/20 text-amber-400',
  FAILED:       'bg-rose-500/20 text-rose-400',
  FAULTY:       'bg-rose-500/20 text-rose-400',
  CANCELLED:    'bg-rose-500/20 text-rose-400',
  MAINTENANCE:  'bg-slate-500/20 text-slate-300',
  OFFLINE:      'bg-slate-500/20 text-slate-300',
  PENDING:      'bg-slate-500/20 text-slate-300',
  ON_LEAVE:     'bg-slate-500/20 text-slate-300',
};

const RISK_CLASSES = {
  'High Risk':   'bg-rose-500/20 text-rose-400',
  'Medium Risk': 'bg-amber-500/20 text-amber-400',
  'Low Risk':    'bg-emerald-500/20 text-emerald-400',
};

const SEVERITY_CLASSES = {
  CRITICAL: 'bg-rose-500/20 text-rose-400',
  SEVERE:   'bg-rose-500/20 text-rose-400',
  HIGH:     'bg-amber-500/20 text-amber-400',
  MODERATE: 'bg-amber-500/20 text-amber-400',
  MEDIUM:   'bg-blue-500/20 text-blue-400',
  LOW:      'bg-blue-500/20 text-blue-400',
};

const PRIORITY_CLASSES = {
  CRITICAL: 'bg-rose-500/20 text-rose-400',
  HIGH:     'bg-amber-500/20 text-amber-400',
  MEDIUM:   'bg-blue-500/20 text-blue-400',
  LOW:      'bg-blue-500/20 text-blue-400',
};

const RESOLUTION_CLASSES = {
  UNRESOLVED:   'bg-rose-500/20 text-rose-400',
  UNDER_REVIEW: 'bg-indigo-500/20 text-indigo-400',
  RESOLVED:     'bg-emerald-500/20 text-emerald-400',
  DISMISSED:    'bg-slate-500/20 text-slate-400',
};

const SIZE_CLASSES = {
  xs:  'text-[10px] px-2 py-0.5',
  sm:  'text-[11px] px-2 py-0.5',
  md:  'text-xs px-2.5 py-1',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

/**
 * @param {'status'|'risk'|'severity'|'priority'|'criticality'|'resolution'} type
 * @param {string}  value   The raw value to display (e.g. "OPERATIONAL", "High Risk")
 * @param {'xs'|'sm'|'md'}  size
 * @param {string}  className  Extra Tailwind classes
 */
export default function StatusBadge({ type = 'status', value, size = 'sm', className = '' }) {
  if (!value) return null;

  let colorClasses = 'bg-slate-500/20 text-slate-300'; // default fallback

  switch (type) {
    case 'risk':
      colorClasses = RISK_CLASSES[value] ?? colorClasses;
      break;
    case 'severity':
      colorClasses = SEVERITY_CLASSES[value?.toUpperCase()] ?? colorClasses;
      break;
    case 'priority':
    case 'criticality':
      colorClasses = PRIORITY_CLASSES[value?.toUpperCase()] ?? colorClasses;
      break;
    case 'resolution':
      colorClasses = RESOLUTION_CLASSES[value?.toUpperCase()] ?? colorClasses;
      break;
    case 'status':
    default:
      colorClasses = STATUS_CLASSES[value?.toUpperCase()] ?? colorClasses;
  }

  const sizeClass = SIZE_CLASSES[size] ?? SIZE_CLASSES.sm;

  return (
    <span
      className={`inline-flex items-center font-semibold rounded whitespace-nowrap ${sizeClass} ${colorClasses} ${className}`}
    >
      {value}
    </span>
  );
}

