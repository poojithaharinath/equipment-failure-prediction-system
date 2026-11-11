import React from 'react';
import {
  LayoutDashboard,
  Factory,
  Activity,
  AlertTriangle,
  Wrench,
  History,
  BrainCircuit,
  ShieldCheck,
  Cpu,
  RefreshCw
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'plants', label: 'Plants & Lines', icon: Factory },
  { id: 'monitoring', label: 'Machine Monitoring', icon: Activity },
  { id: 'predictions', label: 'Failure Prediction', icon: Cpu },
  { id: 'alerts', label: 'Alerts & Exceptions', icon: AlertTriangle },
  { id: 'maintenance', label: 'Maintenance Orders', icon: Wrench },
  { id: 'failures', label: 'Failure History', icon: History },
  { id: 'evaluation', label: 'Model Performance', icon: BrainCircuit },
  { id: 'data-quality', label: 'Data Quality', icon: ShieldCheck },
];

export default function AppLayout({ activeTab, setActiveTab, children }) {
  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/90 flex flex-col shrink-0">
        <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Cpu className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white leading-tight">PREDICT-AI</h1>
            <p className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">Predictive Maintenance</p>
          </div>
        </div>

        {/* Live System Indicator */}
        <div className="px-5 py-3 border-b border-slate-800/60 bg-slate-900/40">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              Telemetry Live
            </span>
            <span className="font-mono text-[10px] text-slate-400">90D / 100 MCH</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Environment Status Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 text-xs text-slate-400 space-y-1">
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500 font-mono">Random Seed</span>
            <span className="font-mono text-slate-300">20261022</span>
          </div>
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500 font-mono">Prediction Horizon</span>
            <span className="font-mono text-emerald-400">Next 24h</span>
          </div>
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500 font-mono">Sensors Monitored</span>
            <span className="font-mono text-slate-300">500 active</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-white capitalize">
              {NAV_ITEMS.find(n => n.id === activeTab)?.label || 'Dashboard'}
            </h2>
            <p className="text-xs text-slate-400">Industrial Equipment Telemetry & Machine Learning Intelligence</p>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
              API: REST (FastAPI)
            </span>
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
              DB: PostgreSQL / SQLite
            </span>
            <button
              onClick={() => window.location.reload()}
              title="Refresh Dashboard"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </header>

        {/* Dynamic Page Container */}
        <main className="flex-1 p-6 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
