import React, { useEffect, useState } from 'react';
import {
  Cpu,
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Search,
  ArrowRight,
  TrendingUp,
  X
} from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { getProbabilityBarColor } from '../utils/formatters';

export default function PredictionsPage({ setSelectedMachineId, setActiveTab }) {
  const [predictions, setPredictions] = useState([]);
  const [selectedPred, setSelectedPred] = useState(null);
  const [filterRisk, setFilterRisk] = useState('ALL'); // 'ALL', 'High Risk', 'Medium Risk', 'Low Risk'
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);

  useEffect(() => {
    loadPredictions();
  }, []);

  const loadPredictions = async () => {
    try {
      setLoading(true);
      const data = await api.getPredictions({ limit: 100 });
      setPredictions(data);
      if (data.length > 0) {
        setSelectedPred(data[0]);
      }
    } catch (err) {
      console.error('Failed to load predictions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchPredict = async () => {
    try {
      setRecomputing(true);
      await api.runBatchPredictions();
      await loadPredictions();
    } catch (err) {
      console.error('Failed to run batch predictions:', err);
    } finally {
      setRecomputing(false);
    }
  };

  const handleInspect = (mId) => {
    if (setSelectedMachineId) setSelectedMachineId(mId);
    if (setActiveTab) setActiveTab('monitoring');
  };

  const filtered = predictions.filter(p => {
    const matchesRisk = filterRisk === 'ALL' || p.risk_category === filterRisk;
    const matchesSearch =
      p.machine_name.toLowerCase().includes(search.toLowerCase()) ||
      p.machine_id.toLowerCase().includes(search.toLowerCase());
    return matchesRisk && matchesSearch;
  });

  const highRiskCount = predictions.filter(p => p.risk_category === 'High Risk').length;
  const medRiskCount = predictions.filter(p => p.risk_category === 'Medium Risk').length;
  const lowRiskCount = predictions.filter(p => p.risk_category === 'Low Risk').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Risk Category Summary Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div
          onClick={() => setFilterRisk('ALL')}
          className={`p-4 rounded-xl border cursor-pointer transition ${
            filterRisk === 'ALL' ? 'bg-slate-800 border-blue-500' : 'bg-slate-900 border-slate-800'
          }`}
        >
          <span className="text-xs text-slate-400 font-medium">All Machines</span>
          <p className="text-2xl font-bold text-white mt-1">{predictions.length}</p>
        </div>

        <div
          onClick={() => setFilterRisk('High Risk')}
          className={`p-4 rounded-xl border cursor-pointer transition ${
            filterRisk === 'High Risk' ? 'bg-rose-950/40 border-rose-500' : 'bg-slate-900 border-slate-800'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-rose-400 font-medium">
            <span>High Risk (&gt;70%)</span>
            <AlertOctagon className="h-4 w-4" />
          </div>
          <p className="text-2xl font-bold text-rose-400 mt-1">{highRiskCount}</p>
        </div>

        <div
          onClick={() => setFilterRisk('Medium Risk')}
          className={`p-4 rounded-xl border cursor-pointer transition ${
            filterRisk === 'Medium Risk' ? 'bg-amber-950/40 border-amber-500' : 'bg-slate-900 border-slate-800'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-amber-400 font-medium">
            <span>Medium Risk (35-70%)</span>
            <AlertTriangle className="h-4 w-4" />
          </div>
          <p className="text-2xl font-bold text-amber-400 mt-1">{medRiskCount}</p>
        </div>

        <div
          onClick={() => setFilterRisk('Low Risk')}
          className={`p-4 rounded-xl border cursor-pointer transition ${
            filterRisk === 'Low Risk' ? 'bg-emerald-950/40 border-emerald-500' : 'bg-slate-900 border-slate-800'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-emerald-400 font-medium">
            <span>Low Risk (&lt;35%)</span>
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <p className="text-2xl font-bold text-emerald-400 mt-1">{lowRiskCount}</p>
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search machine..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <button
          onClick={handleBatchPredict}
          disabled={recomputing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded-lg text-xs font-semibold shadow transition"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${recomputing ? 'animate-spin' : ''}`} />
          {recomputing ? 'Re-scoring All Machines...' : 'Re-evaluate All Predictions'}
        </button>
      </div>

      {/* Main Predictions Grid / Table with Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Machine Probability List */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white text-sm">24-Hour Failure Risk Predictions</h3>
            <span className="text-xs font-mono text-slate-400">{filtered.length} Machines</span>
          </div>

          <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] sticky top-0">
                <tr>
                  <th className="py-2.5 px-3">Machine</th>
                  <th className="py-2.5 px-3">Line</th>
                  <th className="py-2.5 px-3">Health</th>
                  <th className="py-2.5 px-3">Failure Prob</th>
                  <th className="py-2.5 px-3">Risk Level</th>
                  <th className="py-2.5 px-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filtered.map((p) => {
                  const isSelected = selectedPred?.machine_id === p.machine_id;
                  return (
                    <tr
                      key={p.machine_id}
                      onClick={() => setSelectedPred(p)}
                      className={`cursor-pointer transition ${
                        isSelected ? 'bg-blue-950/50' : 'hover:bg-slate-800/40'
                      }`}
                    >
                      <td className="py-2.5 px-3">
                        <div className="font-medium text-white">{p.machine_name}</div>
                        <div className="font-mono text-[10px] text-slate-500">{p.machine_id}</div>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{p.line_id}</td>
                      <td className="py-2.5 px-3 font-semibold text-cyan-400">{p.health_score}%</td>
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${getProbabilityBarColor(p.failure_probability_pct)}`}
                              style={{ width: `${Math.min(100, p.failure_probability_pct)}%` }}
                            />
                          </div>
                          <span className="font-bold text-white text-[11px]">
                            {p.failure_probability_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        <StatusBadge type="risk" value={p.risk_category} size="xs" />
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedPred(p);
                          }}
                          className="text-xs text-blue-400 hover:text-blue-300"
                        >
                          Explain
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Explainability Detail Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm flex flex-col">
          {selectedPred ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-bold text-white text-sm">{selectedPred.machine_name}</h3>
                  <p className="font-mono text-[10px] text-slate-400">{selectedPred.machine_id}</p>
                </div>
                <span
                  className={`px-2 py-1 rounded text-xs font-bold ${
                    selectedPred.risk_category === 'High Risk'
                      ? 'bg-rose-500/20 text-rose-400'
                      : selectedPred.risk_category === 'Medium Risk'
                      ? 'bg-amber-500/20 text-amber-400'
                      : 'bg-emerald-500/20 text-emerald-400'
                  }`}
                >
                  {selectedPred.failure_probability_pct}% Failure Risk
                </span>
              </div>

              {/* Recommendation Callout */}
              <div className="p-3.5 bg-slate-950 rounded-lg border border-slate-800">
                <span className="text-[10px] text-slate-500 font-mono uppercase block mb-1">
                  Model Recommendation
                </span>
                <p className="text-xs text-slate-200 font-medium leading-relaxed">
                  {selectedPred.recommendation}
                </p>
              </div>

              {/* Contributing Sensor Factors */}
              <div>
                <h4 className="text-xs font-semibold text-slate-300 uppercase font-mono mb-2">
                  Top Contributing Risk Factors
                </h4>
                <div className="space-y-2">
                  {selectedPred.contributing_factors.length === 0 ? (
                    <p className="text-xs text-slate-500 py-3 text-center">
                      No abnormal feature deviations detected. Machine operating normally.
                    </p>
                  ) : (
                    selectedPred.contributing_factors.map((factor, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-lg text-xs"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-white">{factor.factor}</span>
                          <span className="font-mono text-[11px] text-rose-400 font-bold">
                            {factor.severity_impact_pct}% impact
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 leading-normal">{factor.detail}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => handleInspect(selectedPred.machine_id)}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition flex items-center justify-center gap-1.5"
              >
                Inspect Telemetry Live <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-xs">
              Select a machine to view ML prediction explanations and sensor factor weights.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

