import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  AlertOctagon,
  ShieldCheck,
  CheckCircle,
  Filter,
  RefreshCw,
  Search,
  Check,
  HelpCircle
} from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { formatTimestamp } from '../utils/formatters';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState(null);

  useEffect(() => {
    loadAlertsData();
  }, []);

  const loadAlertsData = async () => {
    try {
      setLoading(true);
      const [alertsData, metricsData] = await Promise.all([
        api.getAlerts({ page: 1, page_size: 100 }),
        api.getAlertMetrics()
      ]);
      setAlerts(alertsData.items || []);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (issueId, newStatus) => {
    try {
      setResolvingId(issueId);
      await api.updateAlertStatus(issueId, { resolution_status: newStatus });
      setAlerts(prev => prev.map(a => (a.issue_id === issueId ? { ...a, resolution_status: newStatus } : a)));
      const m = await api.getAlertMetrics();
      setMetrics(m);
    } catch (err) {
      console.error('Failed to update alert resolution:', err);
    } finally {
      setResolvingId(null);
    }
  };

  const filtered = alerts.filter(a => {
    const matchSev = severityFilter === 'ALL' || a.severity === severityFilter;
    const matchStatus = statusFilter === 'ALL' || a.resolution_status === statusFilter;
    const matchType = typeFilter === 'ALL' || a.issue_type === typeFilter;
    const matchSearch =
      a.description.toLowerCase().includes(search.toLowerCase()) ||
      a.issue_id.toLowerCase().includes(search.toLowerCase()) ||
      a.related_entity_id.toLowerCase().includes(search.toLowerCase());
    return matchSev && matchStatus && matchType && matchSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Alert KPI Banner */}
      {metrics && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Total Exceptions Logged</p>
              <p className="text-2xl font-bold text-white mt-1">{metrics.total_alerts}</p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-blue-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Unresolved Exceptions</p>
              <p className="text-2xl font-bold text-amber-400 mt-1">{metrics.unresolved_alerts}</p>
            </div>
            <div className="p-3 bg-amber-500/10 rounded-lg">
              <AlertOctagon className="h-6 w-6 text-amber-400" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 font-medium">Critical Unresolved</p>
              <p className="text-2xl font-bold text-rose-500 mt-1">{metrics.critical_unresolved}</p>
            </div>
            <div className="p-3 bg-rose-500/10 rounded-lg">
              <AlertOctagon className="h-6 w-6 text-rose-500" />
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search description, issue ID, entity..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="UNRESOLVED">Unresolved</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          {/* Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
          >
            <option value="ALL">All Exception Types</option>
            <option value="UNKNOWN_SENSOR">Unknown Sensor</option>
            <option value="OUT_OF_RANGE_READING">Out of Range Reading</option>
            <option value="FAILURE_WITHOUT_WARNING">Failure Without Warning</option>
            <option value="INVALID_MAINTENANCE_TIME">Invalid Maintenance Time</option>
            <option value="ZERO_INSTEAD_OF_MISSING">Zero Instead of Missing</option>
          </select>

          <button
            onClick={loadAlertsData}
            title="Refresh Alerts"
            className="p-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 border border-slate-700"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white text-sm">System Exceptions & Edge Cases Audit</h3>
          <span className="text-xs font-mono text-slate-400">{filtered.length} Exceptions</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Issue ID</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Related Entity</th>
                <th className="py-2.5 px-3">Description</th>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-6 text-center text-slate-500">
                    No exceptions matching selected filter criteria.
                  </td>
                </tr>
              ) : (
                filtered.map((a) => (
                  <tr key={a.issue_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-mono font-medium text-slate-300">{a.issue_id}</td>
                    <td className="py-3 px-3">
                      <span className="font-mono text-[11px] text-blue-400 font-semibold">
                        {a.issue_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge type="severity" value={a.severity} size="xs" />
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">{a.related_entity_id}</td>
                    <td className="py-3 px-3 text-slate-300 max-w-sm truncate" title={a.description}>
                      {a.description}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400 whitespace-nowrap">
                      {formatTimestamp(a.timestamp)}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge type="resolution" value={a.resolution_status} size="xs" />
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      {a.resolution_status !== 'RESOLVED' ? (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleResolve(a.issue_id, 'UNDER_REVIEW')}
                            disabled={resolvingId === a.issue_id}
                            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-[11px] font-medium"
                          >
                            Review
                          </button>
                          <button
                            onClick={() => handleResolve(a.issue_id, 'RESOLVED')}
                            disabled={resolvingId === a.issue_id}
                            className="px-2 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-medium"
                          >
                            Resolve
                          </button>
                        </div>
                      ) : (
                        <span className="text-[11px] text-emerald-400 flex items-center justify-end gap-1 font-medium">
                          <Check className="h-3 w-3" /> Resolved
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

