import React, { useEffect, useState } from 'react';
import { Factory, Layers, Cpu, ArrowRight, CheckCircle2, MapPin, Zap } from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function PlantsPage({ setSelectedMachineId, setActiveTab }) {
  const [plants, setPlants] = useState([]);
  const [selectedPlant, setSelectedPlant] = useState(null);
  const [lines, setLines] = useState([]);
  const [selectedLine, setSelectedLine] = useState(null);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPlants();
  }, []);

  const loadPlants = async () => {
    try {
      setLoading(true);
      const data = await api.getPlants();
      setPlants(data);
      if (data.length > 0) {
        selectPlant(data[0]);
      }
    } catch (err) {
      console.error('Failed to load plants:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectPlant = async (plant) => {
    setSelectedPlant(plant);
    try {
      const lineData = await api.getPlantLines(plant.id);
      setLines(lineData);
      if (lineData.length > 0) {
        selectLine(lineData[0]);
      } else {
        setMachines([]);
      }
    } catch (err) {
      console.error('Failed to load lines for plant:', err);
    }
  };

  const selectLine = async (line) => {
    setSelectedLine(line);
    try {
      const mchData = await api.getLineMachines(line.id);
      setMachines(mchData);
    } catch (err) {
      console.error('Failed to load machines for line:', err);
    }
  };

  const handleInspect = (machineId) => {
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

  return (
    <div className="space-y-6">
      {/* Plant Cards Selection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {plants.map((p) => {
          const isSelected = selectedPlant?.id === p.id;
          return (
            <div
              key={p.id}
              onClick={() => selectPlant(p)}
              className={`p-5 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-blue-950/40 border-blue-500 shadow-md shadow-blue-500/10'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-xs text-blue-400 font-semibold">{p.code}</span>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                  {p.status}
                </span>
              </div>
              <h3 className="font-bold text-white text-base mb-1">{p.name}</h3>
              <p className="text-xs text-slate-400 flex items-center gap-1 mb-3">
                <MapPin className="h-3 w-3 text-slate-500" />
                {p.location}
              </p>

              <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 text-xs">
                <div>
                  <span className="text-slate-500 text-[10px] block">Capacity</span>
                  <span className="font-semibold text-slate-200">{p.capacity_mw} MW</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">Lines</span>
                  <span className="font-semibold text-slate-200">{p.line_count}</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">Machines</span>
                  <span className="font-semibold text-slate-200">{p.machine_count}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Production Lines Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-white text-sm flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              Production Lines for {selectedPlant?.name}
            </h3>
            <p className="text-xs text-slate-400">Select a line to explore assigned machines</p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {lines.length} Lines Operational
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {lines.map((l) => {
            const isSelected = selectedLine?.id === l.id;
            return (
              <div
                key={l.id}
                onClick={() => selectLine(l)}
                className={`p-3.5 rounded-lg border cursor-pointer transition ${
                  isSelected
                    ? 'bg-indigo-950/40 border-indigo-500'
                    : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-mono text-[10px] text-slate-400">{l.id}</span>
                  <span className="text-[10px] text-emerald-400 font-semibold">{l.status}</span>
                </div>
                <h4 className="font-medium text-white text-xs mb-1">{l.name}</h4>
                <div className="flex justify-between items-center text-[11px] text-slate-400">
                  <span>Target: {l.target_units_per_hour} u/h</span>
                  <span className="font-mono text-slate-300 font-semibold">{l.machine_count} Machines</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Machine List under Selected Line */}
        <div>
          <div className="flex items-center justify-between mb-3 pt-3 border-t border-slate-800">
            <h4 className="text-xs font-semibold text-slate-300 uppercase font-mono">
              Machines under {selectedLine?.name} ({machines.length} assets)
            </h4>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
                <tr>
                  <th className="py-2.5 px-3">Machine ID</th>
                  <th className="py-2.5 px-3">Name / Type</th>
                  <th className="py-2.5 px-3">Model Number</th>
                  <th className="py-2.5 px-3">Serial Number</th>
                  <th className="py-2.5 px-3">Criticality</th>
                  <th className="py-2.5 px-3">Health Score</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {machines.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-3 font-mono font-medium text-slate-300">{m.id}</td>
                    <td className="py-3 px-3 font-medium text-white">{m.name}</td>
                    <td className="py-3 px-3 font-mono text-slate-400">{m.model_number}</td>
                    <td className="py-3 px-3 font-mono text-slate-400">{m.serial_number}</td>
                    <td className="py-3 px-3">
                      <StatusBadge type="criticality" value={m.criticality} size="xs" />
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`font-semibold ${
                          m.health_score >= 80
                            ? 'text-emerald-400'
                            : m.health_score >= 50
                            ? 'text-amber-400'
                            : 'text-rose-400'
                        }`}
                      >
                        {m.health_score}%
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge type="status" value={m.status} size="xs" />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <button
                        onClick={() => handleInspect(m.id)}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-medium transition"
                      >
                        Inspect Live
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

