import React, { useEffect, useState } from 'react';
import {
  BrainCircuit,
  Award,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  BarChart2,
  Layers,
  TrendingUp
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
import { formatProbability } from '../utils/formatters';

export default function ModelEvaluationPage() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);

  useEffect(() => {
    loadEvaluation();
  }, []);

  const loadEvaluation = async () => {
    try {
      setLoading(true);
      const data = await api.getModelEvaluation();
      setReport(data);
    } catch (err) {
      console.error('Failed to load model evaluation:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetrain = async () => {
    try {
      setTraining(true);
      const res = await api.triggerModelTraining();
      setReport(res.report || res);
    } catch (err) {
      console.error('Failed to retrain model:', err);
    } finally {
      setTraining(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const champion = report?.champion_model;
  const baseline = report?.baseline_model;

  // Feature importances array for chart
  const featData = champion?.feature_importances
    ? Object.entries(champion.feature_importances)
        .map(([feature, importance]) => ({
          feature: feature.replace(/_/g, ' '),
          importance: Math.round(importance * 1000) / 10
        }))
        .sort((a, b) => b.importance - a.importance)
    : [];

  return (
    <div className="space-y-6">
      {/* Top Banner with Retrain Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 p-5 rounded-xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-blue-500" />
            <h3 className="font-bold text-white text-base">Predictive Model Evaluation & Validation</h3>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">
              Random Forest Champion
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Evaluated on holdout chronological test dataset ({report?.test_set_size} samples, {report?.total_test_failures} failure events)
          </p>
        </div>

        <button
          onClick={handleRetrain}
          disabled={training}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white rounded-lg text-xs font-semibold shadow transition"
        >
          <RefreshCw className={`h-4 w-4 ${training ? 'animate-spin' : ''}`} />
          {training ? 'Re-training Models...' : 'Re-train Models'}
        </button>
      </div>

      {/* 5 ML Performance Metric Cards */}
      {champion && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <MetricCard
            label="Accuracy"
            value={formatProbability(champion.accuracy, 1)}
            subtext={`Baseline: ${formatProbability(baseline?.accuracy, 1)}`}
            subtextClassName="text-emerald-400 font-mono"
          />
          <MetricCard
            label="Precision"
            value={formatProbability(champion.precision, 1)}
            valueClassName="text-cyan-400"
            subtext="Low False Positive Rate"
            subtextClassName="text-slate-400 font-mono"
          />
          <MetricCard
            label="Recall"
            value={formatProbability(champion.recall, 1)}
            valueClassName="text-emerald-400"
            subtext="Failure Capture Rate"
            subtextClassName="text-slate-400 font-mono"
          />
          <MetricCard
            label="F1-Score"
            value={formatProbability(champion.f1_score, 1)}
            valueClassName="text-indigo-400"
            subtext="Harmonic Mean"
            subtextClassName="text-slate-400 font-mono"
          />
          <MetricCard
            label="ROC-AUC"
            value={formatProbability(champion.roc_auc, 1)}
            valueClassName="text-purple-400"
            subtext="Discrimination Power"
            subtextClassName="text-slate-400 font-mono"
          />
        </div>
      )}

      {/* Grid: Confusion Matrix & Model Comparison Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix Card */}
        {champion?.confusion_matrix && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
            <h3 className="font-semibold text-white text-sm mb-1">Confusion Matrix</h3>
            <p className="text-xs text-slate-400 mb-4">Actual vs Predicted Equipment Failure (Holdout Test Set)</p>

            <div className="grid grid-cols-2 gap-3 max-w-md mx-auto">
              {/* True Positive */}
              <div className="p-4 bg-emerald-950/40 border border-emerald-500/50 rounded-xl text-center">
                <span className="text-[11px] text-emerald-300 font-semibold uppercase block mb-1">
                  True Positives (Detected)
                </span>
                <p className="text-3xl font-extrabold text-emerald-400">
                  {champion.confusion_matrix.true_positives}
                </p>
                <span className="text-[10px] text-emerald-500/80 mt-1 block">
                  Failures predicted in advance
                </span>
              </div>

              {/* False Positive */}
              <div className="p-4 bg-amber-950/30 border border-amber-500/40 rounded-xl text-center">
                <span className="text-[11px] text-amber-300 font-semibold uppercase block mb-1">
                  False Positives (Alarms)
                </span>
                <p className="text-3xl font-extrabold text-amber-400">
                  {champion.confusion_matrix.false_positives}
                </p>
                <span className="text-[10px] text-amber-500/80 mt-1 block">
                  False alarms issued
                </span>
              </div>

              {/* False Negative */}
              <div className="p-4 bg-rose-950/40 border border-rose-500/50 rounded-xl text-center">
                <span className="text-[11px] text-rose-300 font-semibold uppercase block mb-1">
                  False Negatives (Missed)
                </span>
                <p className="text-3xl font-extrabold text-rose-400">
                  {champion.confusion_matrix.false_negatives}
                </p>
                <span className="text-[10px] text-rose-500/80 mt-1 block">
                  Missed / Sudden failures
                </span>
              </div>

              {/* True Negative */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl text-center">
                <span className="text-[11px] text-slate-400 font-semibold uppercase block mb-1">
                  True Negatives (Nominal)
                </span>
                <p className="text-3xl font-extrabold text-slate-200">
                  {champion.confusion_matrix.true_negatives}
                </p>
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Normal operations confirmed
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Champion vs Baseline Comparison */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-white text-sm mb-1">Model Architecture Comparison</h3>
          <p className="text-xs text-slate-400 mb-4">Random Forest Champion vs Logistic Regression Baseline</p>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Metric</th>
                <th className="py-2.5 px-3">Random Forest</th>
                <th className="py-2.5 px-3">Logistic Regression</th>
                <th className="py-2.5 px-3 text-right">Advantage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              <tr>
                <td className="py-2.5 px-3 text-slate-300 font-medium">Accuracy</td>
                <td className="py-2.5 px-3 font-semibold text-white">{(champion?.accuracy * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-slate-400 font-mono">{(baseline?.accuracy * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-right font-mono text-emerald-400">
                  {((champion?.accuracy - baseline?.accuracy) * 100).toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-300 font-medium">Precision</td>
                <td className="py-2.5 px-3 font-semibold text-white">{(champion?.precision * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-slate-400 font-mono">{(baseline?.precision * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-right font-mono text-emerald-400">
                  {((champion?.precision - baseline?.precision) * 100).toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-300 font-medium">Recall</td>
                <td className="py-2.5 px-3 font-semibold text-white">{(champion?.recall * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-slate-400 font-mono">{(baseline?.recall * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                  {((champion?.recall - baseline?.recall) * 100).toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-300 font-medium">F1-Score</td>
                <td className="py-2.5 px-3 font-semibold text-white">{(champion?.f1_score * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-slate-400 font-mono">{(baseline?.f1_score * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-400">
                  {((champion?.f1_score - baseline?.f1_score) * 100).toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-300 font-medium">ROC-AUC</td>
                <td className="py-2.5 px-3 font-semibold text-white">{(champion?.roc_auc * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-slate-400 font-mono">{(baseline?.roc_auc * 100).toFixed(2)}%</td>
                <td className="py-2.5 px-3 text-right font-mono text-emerald-400">
                  +{((champion?.roc_auc - baseline?.roc_auc) * 100).toFixed(1)}%
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-slate-300 font-medium">Failures Detected</td>
                <td className="py-2.5 px-3 font-semibold text-emerald-400">{champion?.failures_detected_in_advance}</td>
                <td className="py-2.5 px-3 text-slate-400 font-mono">{baseline?.failures_detected_in_advance}</td>
                <td className="py-2.5 px-3 text-right font-mono text-slate-400">Advance</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Feature Importances Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <h3 className="font-semibold text-white text-sm mb-1">Feature Importances (Model Interpretability)</h3>
        <p className="text-xs text-slate-400 mb-4">
          Relative weight of telemetry features in Random Forest failure risk prediction
        </p>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={featData} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
              <XAxis type="number" stroke="#64748b" fontSize={11} unit="%" />
              <YAxis type="category" dataKey="feature" stroke="#94a3b8" fontSize={11} width={130} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                formatter={(val) => [`${val}%`, 'Relative Weight']}
              />
              <Bar dataKey="importance" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                {featData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={index === 0 ? '#3b82f6' : index === 1 ? '#60a5fa' : index === 2 ? '#818cf8' : '#94a3b8'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

