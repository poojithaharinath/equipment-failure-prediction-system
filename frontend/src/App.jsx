import React, { useState } from 'react';
import AppLayout from './layouts/AppLayout';
import DashboardPage from './pages/DashboardPage';
import PlantsPage from './pages/PlantsPage';
import MachineMonitoringPage from './pages/MachineMonitoringPage';
import PredictionsPage from './pages/PredictionsPage';
import AlertsPage from './pages/AlertsPage';
import MaintenancePage from './pages/MaintenancePage';
import FailureHistoryPage from './pages/FailureHistoryPage';
import ModelEvaluationPage from './pages/ModelEvaluationPage';
import DataQualityPage from './pages/DataQualityPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedMachineId, setSelectedMachineId] = useState('MCH-LINE-PLT-001-001-001');

  return (
    <AppLayout activeTab={activeTab} setActiveTab={setActiveTab}>
      {activeTab === 'dashboard' && (
        <DashboardPage
          setActiveTab={setActiveTab}
          setSelectedMachineId={setSelectedMachineId}
        />
      )}
      {activeTab === 'plants' && (
        <PlantsPage
          setActiveTab={setActiveTab}
          setSelectedMachineId={setSelectedMachineId}
        />
      )}
      {activeTab === 'monitoring' && (
        <MachineMonitoringPage
          selectedMachineId={selectedMachineId}
          setSelectedMachineId={setSelectedMachineId}
        />
      )}
      {activeTab === 'predictions' && (
        <PredictionsPage
          setActiveTab={setActiveTab}
          setSelectedMachineId={setSelectedMachineId}
        />
      )}
      {activeTab === 'alerts' && <AlertsPage />}
      {activeTab === 'maintenance' && <MaintenancePage />}
      {activeTab === 'failures' && <FailureHistoryPage />}
      {activeTab === 'evaluation' && <ModelEvaluationPage />}
      {activeTab === 'data-quality' && <DataQualityPage />}
    </AppLayout>
  );
}
