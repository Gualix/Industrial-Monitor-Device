export function renderTechnicalSummary(container, system, settings) {
  const sensors = system?.sensors || {};
  const runtime = system?.runtime || {};

  container.innerHTML = `
    <div class="stack">
      <article class="card">
        <h2>Technical Summary</h2>
        <div class="stack">
          <p><strong>Display:</strong> ${settings?.display_inches || 5}" touch screen</p>
          <p><strong>Buzzer outputs:</strong> GPIO ${(settings?.buzzer_pins || []).join(' and GPIO ')}</p>
          <p><strong>Low pressure threshold:</strong> ${Number(settings?.pressure_low_psi || 0).toFixed(1)} PSI</p>
          <p><strong>High temperature threshold:</strong> ${Number(settings?.temp_high_c || 0).toFixed(1)} °C</p>
          <p><strong>Maintenance interval:</strong> ${Number(settings?.maintenance_interval_hours || 0).toFixed(0)} hours</p>
          <p><strong>Current pressure:</strong> ${Number(sensors.pressure_psi || 0).toFixed(1)} PSI</p>
          <p><strong>Current temperature:</strong> ${Number(sensors.temperature_c || 0).toFixed(1)} °C</p>
          <p><strong>Total runtime:</strong> ${Number(runtime.total_engine_hours || 0).toFixed(1)} h</p>
          <p><strong>Hours since maintenance:</strong> ${Number(runtime.hours_since_maintenance || 0).toFixed(1)} h</p>
        </div>
      </article>

      <article class="card">
        <h2>Maintenance</h2>
        <p class="message">Use the numeric keypad to authenticate before resetting the maintenance counter.</p>
        <button id="resetMaintenanceButton" class="action-button">Reset Maintenance Counter</button>
      </article>
    </div>
  `;
}
