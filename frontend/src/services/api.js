import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const api = {
  // Dashboard
  getDashboardStats: () => client.get('/dashboard/stats').then(res => res.data),

  // Plants & Lines
  getPlants: () => client.get('/plants').then(res => res.data),
  getPlantLines: (plantId) => client.get(`/plants/${plantId}/lines`).then(res => res.data),
  getProductionLines: (params) => client.get('/production-lines', { params }).then(res => res.data),
  getLineMachines: (lineId) => client.get(`/production-lines/${lineId}/machines`).then(res => res.data),

  // Machines
  getMachines: (params) => client.get('/machines', { params }).then(res => res.data),
  getMachine: (machineId) => client.get(`/machines/${machineId}`).then(res => res.data),
  getMachineSensors: (machineId) => client.get(`/machines/${machineId}/sensors`).then(res => res.data),
  getMachineHealthHistory: (machineId) => client.get(`/machines/${machineId}/health-history`).then(res => res.data),
  updateMachine: (machineId, data) => client.patch(`/machines/${machineId}`, data).then(res => res.data),

  // Telemetry
  getTelemetry: (params) => client.get('/telemetry', { params }).then(res => res.data),
  getMachineChartData: (machineId, limit = 60) => client.get(`/telemetry/machine/${machineId}/chart-data`, { params: { limit } }).then(res => res.data),
  getMachineLatestTelemetry: (machineId) => client.get(`/telemetry/machine/${machineId}/latest`).then(res => res.data),
  createTelemetryEvent: (data) => client.post('/telemetry', data).then(res => res.data),

  // Predictions
  getPredictions: (params) => client.get('/predictions', { params }).then(res => res.data),
  getMachinePrediction: (machineId, refresh = false) => client.get(`/predictions/machine/${machineId}`, { params: { refresh } }).then(res => res.data),
  runBatchPredictions: () => client.post('/predictions/batch-predict').then(res => res.data),

  // Work Orders
  getWorkOrders: (params) => client.get('/work-orders', { params }).then(res => res.data),
  getWorkOrder: (woId) => client.get(`/work-orders/${woId}`).then(res => res.data),
  createWorkOrder: (data) => client.post('/work-orders', data).then(res => res.data),
  updateWorkOrderStatus: (woId, data) => client.patch(`/work-orders/${woId}`, data).then(res => res.data),

  // Failure History
  getFailureEvents: (params) => client.get('/failure-events', { params }).then(res => res.data),
  getFailuresSummary: () => client.get('/failure-events/summary').then(res => res.data),

  // Technicians & Parts
  getTechnicians: (params) => client.get('/technicians', { params }).then(res => res.data),
  getParts: (params) => client.get('/parts', { params }).then(res => res.data),

  // Alerts & Exceptions
  getAlerts: (params) => client.get('/alerts', { params }).then(res => res.data),
  updateAlertStatus: (issueId, data) => client.patch(`/alerts/${issueId}`, data).then(res => res.data),
  getAlertMetrics: () => client.get('/alerts/metrics').then(res => res.data),

  // Data Quality & Validation
  getValidationReport: () => client.get('/validation/report').then(res => res.data),
  triggerValidationRun: () => client.post('/validation/run').then(res => res.data),
  getValidationExceptions: (params) => client.get('/validation/exceptions', { params }).then(res => res.data),
  resolveValidationException: (issueId, data) => client.patch(`/validation/exceptions/${issueId}`, data).then(res => res.data),

  // Model Evaluation
  getModelEvaluation: () => client.get('/model-evaluation').then(res => res.data),
  triggerModelTraining: () => client.post('/model-evaluation/train').then(res => res.data),
};

export default api;
