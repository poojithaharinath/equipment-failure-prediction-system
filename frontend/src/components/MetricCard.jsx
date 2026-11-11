/**
 * MetricCard.jsx
 * Reusable KPI / metric card used on Dashboard, Model Evaluation,
 * Failure History and Predictions pages.
 *
 * Usage:
 *   <MetricCard
 *     label="Total Machines"
 *     value={100}
 *     icon={Cpu}
 *     iconColor="text-slate-300"
 *     iconBg="bg-slate-500/10"
 *     subtext="across 3 plants"
 *   />
 *
 *   // With trend indicator
 *   <MetricCard
 *     label="F1-Score"
 *     value="84.4%"
 *     icon={Activity}
 *     iconColor="text-cyan-400"
 *     iconBg="bg-cyan-500/10"
 *     trend={+2.1}
 *     trendLabel="vs last run"
 *   />
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * @param {string}       label         Card title
 * @param {string|number} value        Primary displayed value
 * @param {React.ComponentType} icon   Lucide icon component
 * @param {string}       iconColor     Tailwind text colour class for the icon
 * @param {string}       iconBg        Tailwind background class for the icon container
 * @param {string}       [subtext]     Optional small text below the value
 * @param {number}       [trend]       Numeric change (positive = up, negative = down, 0 = flat)
 * @param {string}       [trendLabel]  Label appended after the trend arrow (e.g. "vs last run")
 * @param {boolean}      [highlight]   When true, adds a subtle coloured border to draw attention
 * @param {string}       [highlightColor] Tailwind border colour class (default: 'border-blue-600')
 * @param {Function}     [onClick]     Optional click handler; card becomes interactive
 * @param {string}       [className]   Extra Tailwind classes on the outer div
 * @param {string}       [valueClassName]  Tailwind classes for the primary value
 * @param {string}       [subtextClassName] Tailwind classes for the subtext line
 */
export default function MetricCard({
  label,
  value,
  icon: Icon,
  iconColor = 'text-blue-400',
  iconBg = 'bg-blue-500/10',
  subtext,
  trend,
  trendLabel,
  highlight = false,
  highlightColor = 'border-blue-600',
  onClick,
  className = '',
  valueClassName = 'text-white',
  subtextClassName = 'text-slate-500',
}) {
  const isClickable = typeof onClick === 'function';

  const trendEl = (() => {
    if (trend == null) return null;
    if (trend > 0)
      return (
        <span className="flex items-center gap-0.5 text-emerald-400 text-[11px] font-semibold">
          <TrendingUp className="h-3 w-3" />+{trend.toFixed(1)}{trendLabel ? ` ${trendLabel}` : ''}
        </span>
      );
    if (trend < 0)
      return (
        <span className="flex items-center gap-0.5 text-rose-400 text-[11px] font-semibold">
          <TrendingDown className="h-3 w-3" />{trend.toFixed(1)}{trendLabel ? ` ${trendLabel}` : ''}
        </span>
      );
    return (
      <span className="flex items-center gap-0.5 text-slate-400 text-[11px]">
        <Minus className="h-3 w-3" />{trendLabel || 'No change'}
      </span>
    );
  })();

  return (
    <div
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onClick={isClickable ? onClick : undefined}
      onKeyDown={isClickable ? (e) => e.key === 'Enter' && onClick() : undefined}
      className={[
        'bg-slate-900 border rounded-xl p-4 flex items-center justify-between shadow-sm transition',
        highlight ? `${highlightColor} border-2` : 'border-slate-800 hover:border-slate-700',
        isClickable ? 'cursor-pointer select-none active:scale-[0.98]' : '',
        className,
      ].join(' ')}
    >
      {/* Text block */}
      <div className="min-w-0 flex-1">
        <p className="text-xs text-slate-400 font-medium truncate">{label}</p>
        <p className={`text-2xl font-bold mt-0.5 leading-none ${valueClassName}`}>{value ?? '—'}</p>
        {subtext && (
          <p className={`text-[11px] mt-1 truncate ${subtextClassName}`}>{subtext}</p>
        )}
        {trendEl && <div className="mt-1.5">{trendEl}</div>}
      </div>

      {/* Icon block */}
      {Icon && (
        <div className={`ml-3 flex-shrink-0 p-3 rounded-lg ${iconBg}`}>
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </div>
      )}
    </div>
  );
}

