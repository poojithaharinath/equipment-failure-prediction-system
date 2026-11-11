import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Search,
  Database,
  Check,
  FileText
} from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function DataQualityPage() {
  const [report, setReport] = useState(null);
  const [exceptions, setExceptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadDataQuality();
  }, []);

  const loadDataQuality = async () => {
    try {
      setLoading(true);
      const [rep, excs] = await Promise.all([
        api.getValidationReport(),
        api.getValidationExceptions({ page_size: 100 })
      ]);
      setReport(rep);
      setExceptions(excs.items || []);
    } catch (err) {
      console.error('Failed to load validation report:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunValidation = async () => {
    try {
      setValidating(true);
      const rep = await api.triggerValidationRun();
      setReport(rep);
      const excs = await api.getValidationExceptions({ page_size: 100 });
      setExceptions(excs.items || []);
    } catch (err) {
      console.error('Failed to run validation suite:', err);
    } finally {
      setValidating(false);
    }
  };

  const handleResolve = async (issueId) => {
    try {
      await api.resolveValidationException(issueId, { resolution_status: 'RESOLVED' });
      setExceptions(prev =>
        prev.map(e => (e.issue_id === issueId ? { ...e, resolution_status: 'RESOLVED' } : e))
      );
    } catch (err) {
      console.error('Failed to resolve exception:', err);
    }
  };

  const filtered = exceptions.filter(e =>
    e.description.toLowerCase().includes(search.toLowerCase()) ||
    e.issue_id.toLowerCase().includes(search.toLowerCase()) ||
    e.issue_type.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const breakdown = report?.breakdown_by_category || {};

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 p-5 rounded-xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            <h3 className="font-bold text-white text-base">Industrial Data Quality & Validation Engine</h3>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
              Automated Integrity Checks Active
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Validating 5 negative scenarios, foreign-key integrity, sensor range limits, and timestamp reconciliation.
          </p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={validating}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 text-white rounded-lg text-xs font-semibold shadow transition"
        >
          <RefreshCw className={`h-4 w-4 ${validating ? 'animate-spin' : ''}`} />
          {validating ? 'Executing Validation Suite...' : 'Run Live Validation Suite'}
        </button>
      </div>

      {/* 5 Edge Case Validation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {/* Edge Case 1: Unknown Sensors */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Negative Scenario 1</span>
          <h4 className="font-semibold text-white text-xs mb-1">Unknown Sensor Readings</h4>
          <p className="text-2xl font-bold text-rose-400 mt-1">{breakdown.unknown_sensors ?? 0}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Unregistered sensor IDs</span>
        </div>

        {/* Edge Case 2: Out of Range / Units */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Negative Scenario 2</span>
          <h4 className="font-semibold text-white text-xs mb-1">Out-of-Range & Invalid Units</h4>
          <p className="text-2xl font-bold text-rose-400 mt-1">{breakdown.out_of_range_or_unit_mismatch ?? 0}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Impossible physical readings</span>
        </div>

        {/* Edge Case 3: Failure without Warning */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Negative Scenario 3</span>
          <h4 className="font-semibold text-white text-xs mb-1">Sudden Failures (0h Lead)</h4>
          <p className="text-2xl font-bold text-amber-400 mt-1">{breakdown.failure_without_lead_warning ?? 0}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Catastrophic sudden events</span>
        </div>

        {/* Edge Case 4: Inverted Maintenance Timestamps */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Negative Scenario 4</span>
          <h4 className="font-semibold text-white text-xs mb-1">Invalid Maintenance Time</h4>
          <p className="text-2xl font-bold text-rose-400 mt-1">{breakdown.invalid_maintenance_timestamps ?? 0}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">End time &lt; Start time</span>
        </div>

        {/* Edge Case 5: Zero instead of missing */}
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl">
          <span className="text-[10px] text-slate-500 uppercase font-mono block mb-1">Negative Scenario 5</span>
          <h4 className="font-semibold text-white text-xs mb-1">Zero Masking Missing Data</h4>
          <p className="text-2xl font-bold text-amber-400 mt-1">{breakdown.zero_instead_of_missing ?? 0}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Dropped sensor values</span>
        </div>
      </div>

      {/* Relational Integrity Checklist (from validation report) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(() => {
          const fkCount = report?.breakdown_by_category?.foreign_key_violations ?? 0;
          const dupCount = report?.breakdown_by_category?.duplicate_records ?? 0;
          return (
            <>
              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {fkCount === 0
                    ? <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                    : <XCircle className="h-6 w-6 text-amber-400 shrink-0" />}
                  <div>
                    <h4 className="text-xs font-semibold text-white">Foreign Key Integrity Across Entities</h4>
                    <p className="text-[11px] text-slate-400">Plants, Lines, Machines, Sensors, Work Orders</p>
                  </div>
                </div>
                <span className={`font-mono text-xs px-2.5 py-1 rounded font-semibold ${fkCount === 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                  {fkCount} Violation{fkCount === 1 ? '' : 's'}
                </span>
              </div>

              <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {dupCount === 0
                    ? <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                    : <XCircle className="h-6 w-6 text-amber-400 shrink-0" />}
                  <div>
                    <h4 className="text-xs font-semibold text-white">Primary Key & Duplicate Telemetry Check</h4>
                    <p className="text-[11px] text-slate-400">Unique timestamps per sensor, non-overwriting</p>
                  </div>
                </div>
                <span className={`font-mono text-xs px-2.5 py-1 rounded font-semibold ${dupCount === 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                  {dupCount} Duplicate{dupCount === 1 ? '' : 's'}
                </span>
              </div>
            </>
          );
        })()}
      </div>

      {/* Exceptions Audit Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="font-semibold text-white text-sm">Documented Data Quality Exceptions</h3>
            <p className="text-xs text-slate-400">Audit trail of non-silent invalid records captured during ingestion</p>
          </div>

          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search exceptions..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Issue ID</th>
                <th className="py-2.5 px-3">Scenario / Type</th>
                <th className="py-2.5 px-3">Severity</th>
                <th className="py-2.5 px-3">Related Entity</th>
                <th className="py-2.5 px-3">Diagnostic Description</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map((e) => (
                <tr key={e.issue_id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 font-mono font-medium text-slate-300">{e.issue_id}</td>
                  <td className="py-3 px-3">
                    <span className="font-mono text-[11px] text-blue-400 font-semibold">{e.issue_type}</span>
                  </td>
                  <td className="py-3 px-3">
                    <StatusBadge type="severity" value={e.severity} size="xs" />
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-400">{e.related_entity_id}</td>
                  <td className="py-3 px-3 text-slate-300 max-w-sm truncate" title={e.description}>
                    {e.description}
                  </td>
                  <td className="py-3 px-3">
                    <StatusBadge type="resolution" value={e.resolution_status} size="xs" />
                  </td>
                  <td className="py-3 px-3 text-right">
                    {e.resolution_status !== 'RESOLVED' ? (
                      <button
                        onClick={() => handleResolve(e.issue_id)}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-medium"
                      >
                        Resolve
                      </button>
                    ) : (
                      <span className="text-[11px] text-emerald-400 flex items-center justify-end gap-1 font-medium">
                        <Check className="h-3 w-3" /> Resolved
                      </span>
                    )}
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

