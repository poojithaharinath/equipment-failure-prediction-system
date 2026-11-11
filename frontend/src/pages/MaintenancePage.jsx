import React, { useEffect, useState } from 'react';
import {
  Wrench,
  Plus,
  Clock,
  CheckCircle,
  AlertTriangle,
  UserCheck,
  Package,
  X,
  Search
} from 'lucide-react';
import api from '../services/api';

export default function MaintenancePage() {
  const [workOrders, setWorkOrders] = useState([]);
  const [machines, setMachines] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [parts, setParts] = useState([]);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  // Modal States
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [selectedWO, setSelectedWO] = useState(null);

  // Form states for creating work order
  const [newWO, setNewWO] = useState({
    machine_id: '',
    priority: 'MEDIUM',
    work_order_type: 'PREVENTIVE',
    description: '',
    root_cause: '',
    scheduled_start_time: new Date().toISOString().slice(0, 16),
    lead_technician_id: '',
    part_id: '',
    part_quantity: 1
  });

  // Form states for updating work order
  const [updateData, setUpdateData] = useState({
    status: 'COMPLETED',
    downtime_minutes: 120,
    cost: 450.0,
    root_cause: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [wos, mchs, techs, prts] = await Promise.all([
        api.getWorkOrders({ page_size: 50 }),
        api.getMachines({ page_size: 100 }),
        api.getTechnicians(),
        api.getParts()
      ]);
      setWorkOrders(wos.items || []);
      setMachines(mchs.items || []);
      setTechnicians(techs || []);
      setParts(prts || []);
      if (mchs.items?.length > 0) {
        setNewWO(prev => ({ ...prev, machine_id: mchs.items[0].id }));
      }
      if (techs?.length > 0) {
        setNewWO(prev => ({ ...prev, lead_technician_id: techs[0].id }));
      }
    } catch (err) {
      console.error('Failed to load maintenance data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        machine_id: newWO.machine_id,
        priority: newWO.priority,
        work_order_type: newWO.work_order_type,
        description: newWO.description,
        root_cause: newWO.root_cause || null,
        scheduled_start_time: new Date(newWO.scheduled_start_time).toISOString(),
        lead_technician_id: newWO.lead_technician_id || null,
        parts_to_use: newWO.part_id ? [{ part_id: newWO.part_id, quantity: Number(newWO.part_quantity) }] : []
      };

      await api.createWorkOrder(payload);
      setShowCreateModal(false);
      await loadData();
    } catch (err) {
      console.error('Failed to create work order:', err);
      alert('Failed to create work order. Check inputs.');
    }
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    if (!selectedWO) return;
    try {
      await api.updateWorkOrderStatus(selectedWO.id, {
        status: updateData.status,
        downtime_minutes: Number(updateData.downtime_minutes),
        cost: Number(updateData.cost),
        root_cause: updateData.root_cause
      });
      setShowUpdateModal(false);
      await loadData();
    } catch (err) {
      console.error('Failed to update work order:', err);
    }
  };

  const openUpdateModal = (wo) => {
    setSelectedWO(wo);
    setUpdateData({
      status: wo.status === 'COMPLETED' ? 'COMPLETED' : 'COMPLETED',
      downtime_minutes: wo.downtime_minutes || 90,
      cost: wo.cost || 350.0,
      root_cause: wo.root_cause || 'Bearing raceway micro-pitting fatigue.'
    });
    setShowUpdateModal(true);
  };

  const filteredWOs = workOrders.filter(wo =>
    statusFilter === 'ALL' || wo.status === statusFilter
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div>
          <h3 className="font-semibold text-white text-sm">Industrial Work Orders & Downtime Tracking</h3>
          <p className="text-xs text-slate-400">Manage corrective, preventive, and emergency repairs</p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-xs text-white focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
          </select>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition"
          >
            <Plus className="h-4 w-4" /> Create Work Order
          </button>
        </div>
      </div>

      {/* Work Orders Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px]">
              <tr>
                <th className="py-2.5 px-3">Order ID</th>
                <th className="py-2.5 px-3">Machine</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Priority</th>
                <th className="py-2.5 px-3">Lead Technician</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3">Downtime</th>
                <th className="py-2.5 px-3">Cost ($)</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredWOs.map((wo) => (
                <tr key={wo.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 font-mono font-medium text-blue-400">{wo.id}</td>
                  <td className="py-3 px-3">
                    <div className="font-medium text-white">{wo.machine_name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{wo.machine_id}</div>
                  </td>
                  <td className="py-3 px-3 text-slate-300">{wo.work_order_type}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        wo.priority === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400'
                          : wo.priority === 'HIGH'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {wo.priority}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-300">{wo.lead_technician_name || 'Unassigned'}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        wo.status === 'COMPLETED'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : wo.status === 'IN_PROGRESS'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-slate-500/20 text-slate-400'
                      }`}
                    >
                      {wo.status}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">
                    {wo.downtime_minutes > 0 ? `${wo.downtime_minutes} min` : '--'}
                  </td>
                  <td className="py-3 px-3 font-mono text-slate-300">${wo.cost.toFixed(2)}</td>
                  <td className="py-3 px-3 text-right">
                    <button
                      onClick={() => openUpdateModal(wo)}
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium transition"
                    >
                      Manage
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Spare Parts Inventory Overview */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-white text-sm flex items-center gap-2">
            <Package className="h-4 w-4 text-emerald-400" />
            Spare Parts Inventory & Unit Stock
          </h3>
          <span className="text-xs font-mono text-slate-400">{parts.length} SKU Catalog</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {parts.map(p => {
            const isLowStock = p.stock_quantity <= p.minimum_reorder_level;
            return (
              <div
                key={p.id}
                className={`p-3 rounded-lg border text-xs ${
                  isLowStock ? 'bg-rose-950/20 border-rose-800' : 'bg-slate-950 border-slate-800'
                }`}
              >
                <div className="flex justify-between items-center text-[10px] text-slate-400 mb-1">
                  <span className="font-mono">{p.part_number}</span>
                  <span className="font-semibold text-slate-300">${p.unit_cost.toFixed(2)}</span>
                </div>
                <h4 className="font-medium text-white truncate" title={p.name}>{p.name}</h4>
                <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-800/60 text-[11px]">
                  <span className="text-slate-400">Stock: {p.stock_quantity} units</span>
                  {isLowStock ? (
                    <span className="text-rose-400 font-bold flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3" /> Reorder
                    </span>
                  ) : (
                    <span className="text-emerald-400">Sufficient</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal: Create Work Order */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="font-bold text-white text-base">New Maintenance Work Order</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Target Machine</label>
                <select
                  value={newWO.machine_id}
                  onChange={(e) => setNewWO({ ...newWO, machine_id: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  required
                >
                  {machines.map(m => (
                    <option key={m.id} value={m.id}>{m.id} — {m.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Priority</label>
                  <select
                    value={newWO.priority}
                    onChange={(e) => setNewWO({ ...newWO, priority: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Order Type</label>
                  <select
                    value={newWO.work_order_type}
                    onChange={(e) => setNewWO({ ...newWO, work_order_type: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    <option value="PREVENTIVE">PREVENTIVE</option>
                    <option value="CORRECTIVE">CORRECTIVE</option>
                    <option value="EMERGENCY">EMERGENCY</option>
                    <option value="INSPECTION">INSPECTION</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Description</label>
                <textarea
                  rows="2"
                  value={newWO.description}
                  onChange={(e) => setNewWO({ ...newWO, description: e.target.value })}
                  placeholder="Describe repair objectives or observed anomalies..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Lead Technician</label>
                  <select
                    value={newWO.lead_technician_id}
                    onChange={(e) => setNewWO({ ...newWO, lead_technician_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    {technicians.map(t => (
                      <option key={t.id} value={t.id}>{t.first_name} {t.last_name} ({t.specialization})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Allocate Replacement Part</label>
                  <select
                    value={newWO.part_id}
                    onChange={(e) => setNewWO({ ...newWO, part_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  >
                    <option value="">None</option>
                    {parts.map(p => (
                      <option key={p.id} value={p.id}>{p.name} (Stock: {p.stock_quantity})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold"
                >
                  Create Work Order
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Update Work Order Status */}
      {showUpdateModal && selectedWO && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-base">Update Order {selectedWO.id}</h3>
                <p className="text-xs text-slate-400">{selectedWO.machine_name}</p>
              </div>
              <button onClick={() => setShowUpdateModal(false)} className="text-slate-400 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleUpdateSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Work Order Status</label>
                <select
                  value={updateData.status}
                  onChange={(e) => setUpdateData({ ...updateData, status: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                >
                  <option value="IN_PROGRESS">IN_PROGRESS</option>
                  <option value="COMPLETED">COMPLETED</option>
                  <option value="CANCELLED">CANCELLED</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Downtime Minutes</label>
                  <input
                    type="number"
                    value={updateData.downtime_minutes}
                    onChange={(e) => setUpdateData({ ...updateData, downtime_minutes: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 mb-1 font-medium">Total Cost ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={updateData.cost}
                    onChange={(e) => setUpdateData({ ...updateData, cost: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-medium">Root Cause & Resolution Notes</label>
                <textarea
                  rows="2"
                  value={updateData.root_cause}
                  onChange={(e) => setUpdateData({ ...updateData, root_cause: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowUpdateModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold"
                >
                  Save Status
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
