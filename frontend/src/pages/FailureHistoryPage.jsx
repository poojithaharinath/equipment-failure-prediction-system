import React, { useEffect, useState } from 'react';
import {
  History,
  AlertOctagon,
  Clock,
  TrendingDown,
  Wrench,
  Search,
  Filter
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import api from '../services/api';

export default function FailureHistoryPage() {
  const [failures, setFailures] = useState([]);
  const [summary, setSummary] = useState(null);
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFailureData();
  }, []);

  const loadFailureData = async () => {
    try {
      setLoading(true);
      const [fData, sData] = await Promise.all([
        api.getFailureEvents({ page_size: 100 }),
        api.getFailuresSummary()
      ]);
      setFailures(fData.items || []);
      setSummary(sData);
    } catch (err) {
      console.error('Failed to load failure history:', err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = failures.filter(f => {
    const matchType = typeFilter === 'ALL' || f.failure_type === typeFilter;
    const matchSev = severityFilter === 'ALL' || f.severity === severityFilter;
    const matchSearch =
      f.machine_name?.toLowerCase().includes(search.toLowerCase()) ||
      f.machine_id.toLowerCase().includes(search.toLowerCase()) ||
      f.root_cause.toLowerCase().includes(search.toLowerCase());
    return matchType && matchSev && matchSearch;
  });

  const pieData = summary?.failures_by_type
    ? Object.entries(summary.failures_by_type).map(([name, value]) => ({ name, value }))
    : [];

  const COLORS = ['#ef4444', '#f97316', '#3b82f6', '#8b5cf6', '#10b981', '#ec4899'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 4 Summary Metric Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Total Historical Failures</p>
              <p className="text-2xl font-bold text-white mt-1">{summary.total_failures}</p>
            </div>
            <div className="p-3 bg-red-500/10 rounded-lg">
              <History className="h-6 w-6 text-red-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Cumulative Downtime</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{summary.total_downtime_hours} hrs</p>
            </div>
            <div className="p-3 bg-amber-500/10 rounded-lg">
              <Clock className="h-6 w-6 text-amber-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Avg Downtime Per Event</p>
              <p className="text-2xl font-bold text-cyan-400 mt-1">{summary.average_downtime_hours} hrs</p>
            </div>
            <div className="p-3 bg-cyan-500/10 rounded-lg">
              <TrendingDown className="h-6 w-6 text-cyan-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Avg Pre-Warning Lead</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1">{summary.average_lead_time_hours} hrs</p>
            </div>
            <div className="p-3 bg-emerald-500/10 rounded-lg">
              <AlertOctagon className="h-6 w-6 text-emerald-400" />
            </div>
          </div>
        </div>
      )}

      {/* Grid: Failure Type Distribution Pie & Filter */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-white text-sm mb-3">Failure Mode Breakdown</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Filters and Search */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-semibold text-white text-sm mb-2">Ground Truth Failure Log</h3>
            <p className="text-xs text-slate-400 mb-4">
              Historical records of confirmed industrial failures, root cause analysis, and associated downtime.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search machine or root cause..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white"
                />
              </div>

              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white"
              >
                <option value="ALL">All Failure Types</option>
                <option value="BEARING_WEAR">Bearing Wear</option>
                <option value="OVERHEATING">Overheating</option>
                <option value="HYDRAULIC_LEAK">Hydraulic Leak</option>
                <option value="MOTOR_BURNOUT">Motor Burnout</option>
                <option value="SENSOR_DRIFT">Sensor Drift</option>
                <option value="MECHANICAL_JAM">Mechanical Jam</option>
              </select>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="SEVERE">Severe</option>
                <option value="MODERATE">Moderate</option>
              </select>
            </div>
          </div>

          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <span>Matching Filtered Events</span>
            <span className="font-mono text-white font-semibold">{filtered.length} Recorded</span>
          </div>
        </div>
      </div>

      {/* Failure Events Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Failure ID</th>
                <th className="py-2.5 px-3">Date / Time</th>
                <th className="py-2.5 px-3">Machine</th>
                <th className="py-2.5 px-3">Failure Mode</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Pre-Warning Lead</th>
                <th className="py-2.5 px-3">Downtime</th>
                <th className="py-2.5 px-3">Root Cause</th>
                <th className="py-2.5 px-3 text-right">Work Order</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map((f) => (
                <tr key={f.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 font-mono font-medium text-rose-400">{f.id}</td>
                  <td className="py-3 px-3 font-mono text-slate-400 whitespace-nowrap">
                    {new Date(f.failure_timestamp).toLocaleDateString()} {new Date(f.failure_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="py-3 px-3">
                    <div className="font-medium text-white">{f.machine_name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{f.machine_id}</div>
                  </td>
                  <td className="py-3 px-3 font-medium text-slate-200">{f.failure_type}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        f.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400'
                          : 'bg-amber-500/20 text-amber-400'
                      }`}
                    >
                      {f.severity}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    {f.pre_warning_lead_time_hours > 0 ? (
                      `${f.pre_warning_lead_time_hours} hrs`
                    ) : (
                      <span className="text-rose-400 font-bold">0.0 hrs (Sudden)</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">{f.downtime_hours} hrs</td>
                  <td className="py-3 px-3 text-slate-300 max-w-xs truncate" title={f.root_cause}>
                    {f.root_cause}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-blue-400">
                    {f.work_order_id || '--'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
