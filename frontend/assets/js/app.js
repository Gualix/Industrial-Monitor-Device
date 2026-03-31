import { getSettings, getSystemState, resetMaintenance } from './api.js';
import { appState } from './state.js';
import { renderDashboard } from './ui/dashboard.js';
import { renderTechnicalSummary } from './ui/technicalSummary.js';
import { updateSystemStatus } from './ui/alarms.js';
import { openKeypadModal } from './ui/keypadModal.js';
import { setupTabs } from './ui/tabs.js';

const dashboardRoot = document.getElementById('dashboard');
const technicalRoot = document.getElementById('technical');
const systemStatus = document.getElementById('systemStatus');

async function loadSettings() {
  appState.settings = await getSettings();
}

async function loadSystemState() {
  appState.system = await getSystemState();
}

function bindMaintenanceButton() {
  const resetButton = document.getElementById('resetMaintenanceButton');
  if (!resetButton) return;

  resetButton.addEventListener('click', async () => {
    const password = await openKeypadModal();
    if (!password) return;

    try {
      await resetMaintenance(password);
      await refresh();
      alert('Maintenance counter reset successfully.');
    } catch (error) {
      alert(error.message || 'Invalid password');
    }
  });
}

function render() {
  renderDashboard(dashboardRoot, appState.system);
  renderTechnicalSummary(technicalRoot, appState.system, appState.settings);
  updateSystemStatus(systemStatus, appState.system);
  bindMaintenanceButton();
}

async function refresh() {
  try {
    await loadSystemState();
    render();
  } catch (error) {
    systemStatus.textContent = 'Connection Error';
    systemStatus.style.color = 'var(--danger)';
  }
}

async function init() {
  setupTabs();
  await loadSettings();
  await refresh();
  window.setInterval(refresh, 2000);
}

init();
