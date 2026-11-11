import React, { useEffect, useState } from 'react';
import {
  Thermometer,
  Activity,
  Gauge,
  Zap,
  RotateCw,
  Search,
  AlertTriangle,
  History,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
  Legend
} from 'recharts';
import api from '../services/api';

export default function MachineMonitoringPage({ selectedMachineId, setSelectedMachineId }) {
  const [machines, setMachines] = useState([]);
  const [machineId, setMachineId] = useState(selectedMachineId || 'MCH-LINE-PLT-001-001-001');
  const [machine, setMachine] = useState(null);
  const [latestTelemetry, setLatestTelemetry] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [healthHistory, setHealthHistory] = useState([]);
  const [activeMetric, setActiveMetric] = useState('all'); // 'all', 'temperature', 'vibration', 'pressure', 'current', 'rpm'
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadMachineList();
  }, []);

  useEffect(() => {
    if (selectedMachineId) {
      setMachineId(selectedMachineId);
    }
  }, [selectedMachineId]);

  useEffect(() => {
    if (machineId) {
      loadMachineDetails(machineId);
    }
  }, [machineId]);

  const loadMachineList = async () => {
    try {
      const data = await api.getMachines({ page_size: 100 });
      setMachines(data.items || []);
      if (!selectedMachineId && data.items && data.items.length > 0) {
        setMachineId(data.items[0].id);
      }
    } catch (err) {
      console.error('Failed to load machine list:', err);
    }
  };

  const loadMachineDetails = async (id) => {
    try {
      setLoading(true);
      const [mch, latest, chart, audits] = await Promise.all([
        api.getMachine(id),
        api.getMachineLatestTelemetry(id),
        api.getMachineChartData(id, 60),
        api.getMachineHealthHistory(id, 20)
      ]);
      setMachine(mch);
      setLatestTelemetry(latest);
      setChartData(chart);
      setHealthHistory(audits);
    } catch (err) {
      console.error('Failed to load machine data:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredMachines = machines.filter(m =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.id.toLowerCase().includes(search.toLowerCase())
  );

  const getMetricStatus = (metricKey) => {
    if (!latestTelemetry || !latestTelemetry[metricKey]) return { color: 'text-slate-400', label: 'NOMINAL' };
    const { value, min_threshold, max_threshold, is_anomaly } = latestTelemetry[metricKey];
    if (is_anomaly || value > max_threshold || value < min_threshold) {
      return { color: 'text-rose-400', label: 'WARNING / ANOMALY', bg: 'bg-rose-500/10 border-rose-500/40' };
    }
    return { color: 'text-emerald-400', label: 'NORMAL', bg: 'bg-slate-900 border-slate-800' };
  };

  return (
    <div className="space-y-6">
      {/* Top Machine Selector & Metadata Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1 max-w-md relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search machine name or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex-1 max-w-md">
            <select
              value={machineId}
              onChange={(e) => {
                setMachineId(e.target.value);
                if (setSelectedMachineId) setSelectedMachineId(e.target.value);
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
            >
              {filteredMachines.map(m => (
                <option key={m.id} value={m.id}>
                  {m.id} — {m.name} ({m.health_score}%)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Machine Quick Summary Details */}
        {machine && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4 pt-4 border-t border-slate-800/80 text-xs">
            <div>
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Status</span>
              <span className={`font-semibold ${machine.status === 'OPERATIONAL' ? 'text-emerald-400' : 'text-amber-400'}`}>
                {machine.status}
              </span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Health Score</span>
              <span className="font-semibold text-cyan-400">{machine.health_score}%</span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Machine Type</span>
              <span className="text-slate-200">{machine.machine_type}</span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Criticality</span>
              <span className="font-semibold text-rose-400">{machine.criticality}</span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block uppercase font-mono">Operating Hours</span>
              <span className="text-slate-200 font-mono">{machine.operating_hours} hrs</span>
            </div>
            <div>
              <span className="text-slate-500 text-[10px] block uppercase font-mono">24h Failure Prob</span>
              <span className={`font-bold ${machine.failure_probability_pct > 50 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {machine.failure_probability_pct}% ({machine.risk_category})
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 5 Real-Time Telemetry Cards */}
      {latestTelemetry && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Temperature */}
          <div className={`p-4 rounded-xl border transition ${getMetricStatus('temperature').bg}`}>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <Thermometer className="h-4 w-4 text-orange-400" />
                Temperature
              </span>
              <span className={`text-[10px] font-semibold ${getMetricStatus('temperature').color}`}>
                {getMetricStatus('temperature').label}
              </span>
            </div>
            <p className="text-2xl font-bold text-white">
              {latestTelemetry.temperature?.value ?? '--'} <span className="text-xs text-slate-400 font-normal">°C</span>
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Bounds: {latestTelemetry.temperature?.min_threshold}°C - {latestTelemetry.temperature?.max_threshold}°C
            </p>
          </div>

          {/* Vibration */}
          <div className={`p-4 rounded-xl border transition ${getMetricStatus('vibration').bg}`}>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <Activity className="h-4 w-4 text-purple-400" />
                Vibration
              </span>
              <span className={`text-[10px] font-semibold ${getMetricStatus('vibration').color}`}>
                {getMetricStatus('vibration').label}
              </span>
            </div>
            <p className="text-2xl font-bold text-white">
              {latestTelemetry.vibration?.value ?? '--'} <span className="text-xs text-slate-400 font-normal">mm/s</span>
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Bounds: {latestTelemetry.vibration?.min_threshold} - {latestTelemetry.vibration?.max_threshold} mm/s
            </p>
          </div>

          {/* Pressure */}
          <div className={`p-4 rounded-xl border transition ${getMetricStatus('pressure').bg}`}>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <Gauge className="h-4 w-4 text-blue-400" />
                Pressure
              </span>
              <span className={`text-[10px] font-semibold ${getMetricStatus('pressure').color}`}>
                {getMetricStatus('pressure').label}
              </span>
            </div>
            <p className="text-2xl font-bold text-white">
              {latestTelemetry.pressure?.value ?? '--'} <span className="text-xs text-slate-400 font-normal">Bar</span>
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Bounds: {latestTelemetry.pressure?.min_threshold} - {latestTelemetry.pressure?.max_threshold} Bar
            </p>
          </div>

          {/* Current */}
          <div className={`p-4 rounded-xl border transition ${getMetricStatus('current').bg}`}>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <Zap className="h-4 w-4 text-yellow-400" />
                Current
              </span>
              <span className={`text-[10px] font-semibold ${getMetricStatus('current').color}`}>
                {getMetricStatus('current').label}
              </span>
            </div>
            <p className="text-2xl font-bold text-white">
              {latestTelemetry.current?.value ?? '--'} <span className="text-xs text-slate-400 font-normal">A</span>
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Bounds: {latestTelemetry.current?.min_threshold} - {latestTelemetry.current?.max_threshold} A
            </p>
          </div>

          {/* RPM */}
          <div className={`p-4 rounded-xl border transition ${getMetricStatus('rpm').bg}`}>
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-slate-400 flex items-center gap-1.5 font-medium">
                <RotateCw className="h-4 w-4 text-emerald-400" />
                Speed (RPM)
              </span>
              <span className={`text-[10px] font-semibold ${getMetricStatus('rpm').color}`}>
                {getMetricStatus('rpm').label}
              </span>
            </div>
            <p className="text-2xl font-bold text-white">
              {latestTelemetry.rpm?.value ?? '--'} <span className="text-xs text-slate-400 font-normal">RPM</span>
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">
              Bounds: {latestTelemetry.rpm?.min_threshold} - {latestTelemetry.rpm?.max_threshold} RPM
            </p>
          </div>
        </div>
      )}

      {/* Historical Telemetry Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="font-semibold text-white text-sm">Telemetry Time Series & Anomaly Trace</h3>
            <p className="text-xs text-slate-400">Historical sensor trends with anomaly detection triggers</p>
          </div>

          {/* Metric Selector Tabs */}
          <div className="flex flex-wrap gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {[
              { id: 'all', label: 'Overview' },
              { id: 'temperature', label: 'Temperature' },
              { id: 'vibration', label: 'Vibration' },
              { id: 'pressure', label: 'Pressure' },
              { id: 'current', label: 'Current' },
              { id: 'rpm', label: 'RPM' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveMetric(tab.id)}
                className={`px-2.5 py-1 rounded text-xs transition ${
                  activeMetric === tab.id
                    ? 'bg-blue-600 text-white font-medium'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="h-80">
          {chartData?.points && chartData.points.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData.points} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="formatted_time" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Legend wrapperStyle={{ paddingTop: '10px' }} />

                {(activeMetric === 'all' || activeMetric === 'temperature') && (
                  <Line type="monotone" dataKey="temperature" name="Temp (°C)" stroke="#f97316" strokeWidth={2} dot={false} />
                )}
                {(activeMetric === 'all' || activeMetric === 'vibration') && (
                  <Line type="monotone" dataKey="vibration" name="Vibration (mm/s)" stroke="#c084fc" strokeWidth={2} dot={false} />
                )}
                {(activeMetric === 'all' || activeMetric === 'pressure') && (
                  <Line type="monotone" dataKey="pressure" name="Pressure (Bar)" stroke="#38bdf8" strokeWidth={2} dot={false} />
                )}
                {(activeMetric === 'all' || activeMetric === 'current') && (
                  <Line type="monotone" dataKey="current" name="Current (A)" stroke="#facc15" strokeWidth={2} dot={false} />
                )}
                {(activeMetric === 'rpm') && (
                  <Line type="monotone" dataKey="rpm" name="RPM" stroke="#34d399" strokeWidth={2} dot={false} />
                )}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              No historical telemetry readings logged for this machine yet.
            </div>
          )}
        </div>
      </div>

      {/* Health Audit History */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="font-semibold text-white text-sm flex items-center gap-2 mb-3">
          <History className="h-4 w-4 text-cyan-400" />
          Machine Health & Status Transition Audit Trail
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Timestamp</th>
                <th className="py-2.5 px-3">Trigger Event</th>
                <th className="py-2.5 px-3">Previous Status</th>
                <th className="py-2.5 px-3">New Status</th>
                <th className="py-2.5 px-3">Previous Score</th>
                <th className="py-2.5 px-3">New Score</th>
                <th className="py-2.5 px-3">Failure Prob</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {healthHistory.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-4 text-center text-slate-500">
                    No status transition events logged for this asset.
                  </td>
                </tr>
              ) : (
                healthHistory.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2 px-3 font-mono text-slate-400">{h.timestamp}</td>
                    <td className="py-2 px-3 font-medium text-white">{h.trigger_event}</td>
                    <td className="py-2 px-3 text-slate-400">{h.previous_status}</td>
                    <td className="py-2 px-3">
                      <span className="font-semibold text-emerald-400">{h.new_status}</span>
                    </td>
                    <td className="py-2 px-3 text-slate-400">{h.previous_health_score}%</td>
                    <td className="py-2 px-3 font-semibold text-cyan-400">{h.new_health_score}%</td>
                    <td className="py-2 px-3 font-mono text-slate-300">
                      {h.failure_probability ? `${round(h.failure_probability * 100, 1)}%` : '--'}
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

function round(val, digits = 1) {
  return Number(val).toFixed(digits);
}
