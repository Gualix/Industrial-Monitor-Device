function badgeClass(active) {
  return active ? 'badge active' : 'badge';
}

function statusText(active) {
  return active ? 'ACTIVE' : 'OK';
}

export function renderDashboard(container, system) {
  const sensors = system?.sensors || {};
  const runtime = system?.runtime || {};
  const alarms = sensors.alarms || {};

  container.innerHTML = `
    <div class="stack">
      <div class="card-grid">
        <article class="card">
          <h2>Oil Pressure</h2>
          <div class="metric">${Number(sensors.pressure_psi || 0).toFixed(1)} PSI</div>
          <div class="submetric">Voltage: ${Number(sensors.pressure_voltage || 0).toFixed(2)} V</div>
        </article>

        <article class="card">
          <h2>Temperature</h2>
          <div class="metric">${Number(sensors.temperature_c || 0).toFixed(1)} °C</div>
          <div class="submetric">Engine: ${sensors.engine_on ? 'ON' : 'OFF'}</div>
        </article>

        <article class="card">
          <h2>Total Hourmeter</h2>
          <div class="metric">${Number(runtime.total_engine_hours || 0).toFixed(1)} h</div>
          <div class="submetric">Persistent engine runtime</div>
        </article>

        <article class="card">
          <h2>Since Maintenance</h2>
          <div class="metric">${Number(runtime.hours_since_maintenance || 0).toFixed(1)} h</div>
          <div class="submetric">Oil change interval tracking</div>
        </article>
      </div>

      <article class="card">
        <h2>Alarm Status</h2>
        <div class="alarm-list">
          <div class="alarm-item ${alarms.low_pressure ? 'active' : ''}">
            <span>Low pressure</span>
            <span class="${badgeClass(alarms.low_pressure)}">${statusText(alarms.low_pressure)}</span>
          </div>
          <div class="alarm-item ${alarms.high_temperature ? 'active' : ''}">
            <span>High temperature</span>
            <span class="${badgeClass(alarms.high_temperature)}">${statusText(alarms.high_temperature)}</span>
          </div>
          <div class="alarm-item ${alarms.maintenance_due ? 'active' : ''}">
            <span>Maintenance due</span>
            <span class="${badgeClass(alarms.maintenance_due)}">${statusText(alarms.maintenance_due)}</span>
          </div>
        </div>
      </article>
    </div>
  `;
}
