import React from 'react';
import {
  Factory,
  Layers,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  XCircle,
  Activity,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import api from '../services/api';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import { useApi } from '../hooks/useApi';

export default function DashboardPage({ setActiveTab, setSelectedMachineId }) {
  const { data: stats, loading, error, refresh } = useApi(() => api.getDashboardStats(), []);

  const handleInspectMachine = (machineId) => {
    if (setSelectedMachineId) setSelectedMachineId(machineId);
    if (setActiveTab) setActiveTab('monitoring');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-950/40 border border-red-800 rounded-xl text-red-200">
        <h3 className="font-bold text-lg mb-2">Backend Connection Error</h3>
        <p>Could not connect to backend API. Please ensure FastAPI server is running on port 8000.</p>
        <button
          onClick={refresh}
          className="mt-4 px-4 py-2 bg-red-800 hover:bg-red-700 rounded-lg text-white font-medium"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const kpis = [
    { label: 'Total Plants', value: stats.total_plants, icon: Factory, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Production Lines', value: stats.total_production_lines, icon: Layers, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
    { label: 'Total Machines', value: stats.total_machines, icon: Cpu, color: 'text-slate-300', bg: 'bg-slate-500/10' },
    { label: 'Healthy Machines', value: stats.healthy_machines, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { label: 'Medium-Risk Machines', value: stats.medium_risk_machines, icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { label: 'High-Risk Machines', value: stats.high_risk_machines, icon: AlertOctagon, color: 'text-rose-400', bg: 'bg-rose-500/10' },
    { label: 'Failed Machines', value: stats.failed_machines, icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
    { label: 'Average Health Score', value: `${stats.average_machine_health}%`, icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
  ];

  return (
    <div className="space-y-6">
      {/* 8 Main KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <MetricCard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            icon={kpi.icon}
            iconColor={kpi.color}
            iconBg={kpi.bg}
          />
        ))}
      </div>

      {/* Grid: Health Chart & Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Machine Health Score Distribution */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white text-sm">Overall Machine Health Distribution</h3>
              <p className="text-xs text-slate-400">Distribution of active machines by current health score</p>
            </div>
            <span className="text-xs font-mono px-2 py-1 bg-slate-800 rounded text-slate-300">
              {stats.total_machines} Total Assets
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.health_distribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="range" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f8fafc', fontWeight: 'bold' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {stats.health_distribution.map((entry, index) => {
                    const colors = ['#ef4444', '#f97316', '#f59e0b', '#3b82f6', '#10b981'];
                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Alerts Feed */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-white text-sm flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-400" />
              Recent System Alerts
            </h3>
            <button
              onClick={() => setActiveTab('alerts')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              View All <ArrowRight className="h-3 w-3" />
            </button>
          </div>

          <div className="flex-1 space-y-2.5 overflow-y-auto max-h-64 pr-1">
            {stats.recent_alerts.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No active alerts recorded.</p>
            ) : (
              stats.recent_alerts.map((alert) => (
                <div
                  key={alert.issue_id}
                  className="p-2.5 bg-slate-950/60 border border-slate-800/80 rounded-lg text-xs hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-[10px] text-slate-400">{alert.issue_type}</span>
                    <StatusBadge type="severity" value={alert.severity} size="xs" />
                  </div>
                  <p className="text-slate-300 line-clamp-2">{alert.description}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Machines Requiring Immediate Attention */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-white text-sm flex items-center gap-2">
              <AlertOctagon className="h-4 w-4 text-rose-500" />
              Machines Requiring Immediate Engineering Attention
            </h3>
            <p className="text-xs text-slate-400">Machines with highest failure probability in next 24 hours</p>
          </div>
          <button
            onClick={() => setActiveTab('predictions')}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium"
          >
            All Predictions <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Machine ID</th>
                <th className="py-2.5 px-3">Name / Type</th>
                <th className="py-2.5 px-3">Production Line</th>
                <th className="py-2.5 px-3">Health Score</th>
                <th className="py-2.5 px-3">24h Failure Prob</th>
                <th className="py-2.5 px-3">Recommended Action</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {stats.machines_requiring_attention.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-6 text-center text-slate-500">
                    All machines are currently operating within nominal parameters.
                  </td>
                </tr>
              ) : (
                stats.machines_requiring_attention.map((m) => (
                  <tr key={m.machine_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-mono font-medium text-slate-300">{m.machine_id}</td>
                    <td className="py-3 px-3">
                      <div className="font-medium text-white">{m.machine_name}</div>
                      <div className="text-[10px] text-slate-400">{m.machine_type}</div>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-400">{m.line_id}</td>
                    <td className="py-3 px-3">
                      <span className="font-semibold text-rose-400">{m.health_score}%</span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400">
                        {m.failure_probability_pct}%
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-300 max-w-xs truncate">{m.recommendation}</td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleInspectMachine(m.machine_id)}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition"
                      >
                        Inspect
                      </button>
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

