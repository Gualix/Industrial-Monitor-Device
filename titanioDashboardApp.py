from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import os
import json
import time
import glob
import smbus
from datetime import datetime

app = Flask(__name__)
app.secret_key = "titanio_secret_change_me"

# =========================
# CONFIGURACIÓN
# =========================
DATA_DIR = "data"
RUNTIME_FILE = os.path.join(DATA_DIR, "runtime.json")
LOG_FILE = os.path.join(DATA_DIR, "log.csv")
PASSWORD = "2026"

OIL_CHANGE_INTERVAL_HOURS = 500.0
SAVE_INTERVAL = 5
READ_INTERVAL = 2

ADS1115_ADDR = 0x48
REG_CONVERSION = 0x00
REG_CONFIG = 0x01
ADS_CONFIG = 0x42C3  # A0, ±4.096V, modo continuo

TEMP_HIGH_LIMIT_C = 100.0
PRESSURE_LOW_LIMIT_PSI = 10.0
PRESSURE_VOLT_MIN = 0.5
PRESSURE_VOLT_MAX = 4.5
PRESSURE_PSI_MAX = 150.0

os.makedirs(DATA_DIR, exist_ok=True)
bus = smbus.SMBus(1)

base_dir = "/sys/bus/w1/devices/"
device_folders = glob.glob(base_dir + "28-*")
device_file = device_folders[0] + "/w1_slave" if device_folders else None


def log_event(event, details=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        if new_file:
            f.write("timestamp,event,details\n")
        f.write(f'{now},{event},{details}\n')


def atomic_write_json(path, data):
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_path, path)


def load_runtime():
    if not os.path.exists(RUNTIME_FILE):
        data = {
            "total_hours": 0.0,
            "oil_hours": 0.0,
            "last_update": time.time(),
            "oil_changes": 0,
            "last_oil_change_at": "",
            "last_reset_by": "system"
        }
        atomic_write_json(RUNTIME_FILE, data)
        return data

    with open(RUNTIME_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_runtime(data):
    data["last_update"] = time.time()
    atomic_write_json(RUNTIME_FILE, data)


def read_temp():
    if not device_file:
        return None
    try:
        with open(device_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        attempts = 0
        while lines and lines[0].strip()[-3:] != "YES" and attempts < 5:
            time.sleep(0.2)
            with open(device_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            attempts += 1

        if len(lines) < 2:
            return None

        temp_pos = lines[1].find("t=")
        if temp_pos != -1:
            return float(lines[1][temp_pos + 2:]) / 1000.0
    except Exception:
        return None
    return None


def read_ads_voltage():
    try:
        bus.write_i2c_block_data(
            ADS1115_ADDR,
            REG_CONFIG,
            [(ADS_CONFIG >> 8) & 0xFF, ADS_CONFIG & 0xFF]
        )
        time.sleep(0.1)
        data = bus.read_i2c_block_data(ADS1115_ADDR, REG_CONVERSION, 2)
        raw_adc = (data[0] << 8) | data[1]
        if raw_adc > 32767:
            raw_adc -= 65536
        return raw_adc * 4.096 / 32768.0
    except Exception:
        return None


def voltage_to_psi(voltage):
    if voltage is None:
        return None
    psi = (voltage - PRESSURE_VOLT_MIN) * (PRESSURE_PSI_MAX / (PRESSURE_VOLT_MAX - PRESSURE_VOLT_MIN))
    return max(0.0, min(PRESSURE_PSI_MAX, psi))


def update_runtime_hours(runtime_data):
    now_ts = time.time()
    elapsed_hours = max(0.0, (now_ts - runtime_data.get("last_update", now_ts)) / 3600.0)
    runtime_data["total_hours"] = runtime_data.get("total_hours", 0.0) + elapsed_hours
    runtime_data["oil_hours"] = runtime_data.get("oil_hours", 0.0) + elapsed_hours
    runtime_data["last_update"] = now_ts
    return runtime_data


def format_hours(hours):
    total_seconds = int(hours * 3600)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:05d}:{m:02d}:{s:02d}"


def read_last_logs(limit=25):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]
    rows = []
    for line in reversed(lines[-limit:]):
        parts = line.strip().split(",", 2)
        if len(parts) == 3:
            rows.append({"timestamp": parts[0], "event": parts[1], "details": parts[2]})
    return rows


def current_snapshot():
    runtime_data = load_runtime()
    runtime_data = update_runtime_hours(runtime_data)
    save_runtime(runtime_data)

    temp_c = read_temp()
    voltage = read_ads_voltage()
    psi = voltage_to_psi(voltage)

    alarms = []
    if temp_c is None:
        alarms.append("Sensor de temperatura no disponible")
    elif temp_c > TEMP_HIGH_LIMIT_C:
        alarms.append("Temperatura alta")

    if psi is None:
        alarms.append("Sensor de presión no disponible")
    elif psi < PRESSURE_LOW_LIMIT_PSI:
        alarms.append("Baja presión de aceite")

    if runtime_data["oil_hours"] >= OIL_CHANGE_INTERVAL_HOURS:
        alarms.append("Cambio de aceite requerido")

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "temp_c": temp_c,
        "voltage": voltage,
        "psi": psi,
        "total_hours": runtime_data["total_hours"],
        "oil_hours": runtime_data["oil_hours"],
        "oil_changes": runtime_data.get("oil_changes", 0),
        "last_oil_change_at": runtime_data.get("last_oil_change_at", ""),
        "alarms": alarms,
        "status": "ALERTA" if alarms else "NORMAL",
        "maintenance_due": runtime_data["oil_hours"] >= OIL_CHANGE_INTERVAL_HOURS,
        "total_hours_fmt": format_hours(runtime_data["total_hours"]),
        "oil_hours_fmt": format_hours(runtime_data["oil_hours"]),
    }


HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TITANIO Monitor</title>
  <style>
    :root {
      --bg: #0b1220;
      --card: #121a2b;
      --card-2: #182238;
      --text: #e8edf7;
      --muted: #9ba8c7;
      --ok: #12c48b;
      --warn: #ffb020;
      --danger: #ff5d5d;
      --accent: #53a8ff;
      --border: rgba(255,255,255,.08);
      --shadow: 0 12px 30px rgba(0,0,0,.25);
      --radius: 22px;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, system-ui, Arial, sans-serif;
      background: linear-gradient(180deg, #08101d, #0d1627 35%, #09111d);
      color: var(--text);
    }

    .wrap {
      max-width: 1080px;
      margin: 0 auto;
      padding: 16px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
    }

    .brand {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .brand h1 {
      margin: 0;
      font-size: 1.4rem;
      letter-spacing: .02em;
    }

    .brand p {
      margin: 0;
      color: var(--muted);
      font-size: .92rem;
    }

    .status-badge {
      padding: 10px 14px;
      border-radius: 999px;
      font-weight: 700;
      background: rgba(18,196,139,.16);
      color: #8bf0c9;
      border: 1px solid rgba(18,196,139,.25);
    }

    .status-badge.alert { background: rgba(255,93,93,.14); color: #ff9f9f; border-color: rgba(255,93,93,.22); }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 14px;
    }

    .card {
      background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 18px;
    }

    .metric { grid-column: span 3; }
    .wide { grid-column: span 6; }
    .full { grid-column: span 12; }

    .label {
      color: var(--muted);
      font-size: .9rem;
      margin-bottom: 10px;
    }

    .value {
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: -.03em;
    }

    .sub {
      margin-top: 8px;
      color: var(--muted);
      font-size: .9rem;
    }

    .alarm-list {
      display: grid;
      gap: 10px;
      margin-top: 8px;
    }

    .alarm {
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(255,93,93,.12);
      border: 1px solid rgba(255,93,93,.16);
      font-weight: 700;
    }

    .ok-box {
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(18,196,139,.12);
      border: 1px solid rgba(18,196,139,.18);
      font-weight: 700;
      color: #91f0ce;
    }

    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
    }

    input[type=password], select {
      width: 100%;
      background: var(--card-2);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 12px 14px;
      border-radius: 14px;
      font-size: 1rem;
    }

    button {
      border: none;
      border-radius: 14px;
      padding: 12px 16px;
      font-size: 1rem;
      font-weight: 700;
      background: var(--accent);
      color: white;
      cursor: pointer;
    }

    button.secondary { background: #24334f; }
    button.danger { background: var(--danger); }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: .94rem;
    }

    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }

    th { color: var(--muted); font-weight: 600; }
    .muted { color: var(--muted); }
    .flash { margin-bottom: 12px; padding: 12px 14px; border-radius: 14px; font-weight: 700; }
    .flash.ok { background: rgba(18,196,139,.12); border: 1px solid rgba(18,196,139,.2); color: #9bf3d4; }
    .flash.err { background: rgba(255,93,93,.12); border: 1px solid rgba(255,93,93,.2); color: #ffadad; }

    @media (max-width: 820px) {
      .metric, .wide { grid-column: span 12; }
      .topbar { flex-direction: column; align-items: stretch; }
      .status-badge { text-align: center; }
      .wrap { padding: 12px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div class="brand">
        <h1>TITANIO Company</h1>
        <p>Industrial Monitor Device</p>
      </div>
      <div id="statusBadge" class="status-badge">Cargando...</div>
    </div>

    <div id="flashBox"></div>

    <div class="grid">
      <div class="card metric">
        <div class="label">Temperatura</div>
        <div class="value" id="tempValue">--</div>
        <div class="sub">Límite de alarma: 100 °C</div>
      </div>

      <div class="card metric">
        <div class="label">Presión de aceite</div>
        <div class="value" id="psiValue">--</div>
        <div class="sub">Alarma por debajo de 10 PSI</div>
      </div>

      <div class="card metric">
        <div class="label">Horímetro total</div>
        <div class="value" id="totalHoursValue">--</div>
        <div class="sub">Acumulado persistente</div>
      </div>

      <div class="card metric">
        <div class="label">Horas desde cambio de aceite</div>
        <div class="value" id="oilHoursValue">--</div>
        <div class="sub">Cambio recomendado cada 500 h</div>
      </div>

      <div class="card wide">
        <div class="label">Estado del sistema</div>
        <div id="alarmsBox"></div>
        <div class="sub" id="timestampBox">--</div>
      </div>

      <div class="card wide">
        <div class="label">Mantenimiento protegido</div>
        <form method="post" action="/maintenance" class="controls" style="display:grid;gap:10px;">
          <input type="password" name="password" placeholder="Contraseña">
          <select name="action">
            <option value="reset_oil">Reiniciar horas de aceite</option>
            <option value="reset_total">Reiniciar horímetro total</option>
            <option value="reset_both">Reiniciar ambos valores</option>
          </select>
          <button type="submit">Aplicar cambio</button>
        </form>
        <div class="sub">Contraseña requerida: protegida en el sistema. Cada cambio queda registrado en log.</div>
      </div>

      <div class="card full">
        <div class="label">Resumen técnico</div>
        <table>
          <tbody>
            <tr><th>Voltaje ADS1115</th><td id="voltageValue">--</td></tr>
            <tr><th>Cambios de aceite registrados</th><td id="oilChangesValue">--</td></tr>
            <tr><th>Último cambio de aceite</th><td id="lastOilChangeValue">--</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card full">
        <div class="label">Últimos eventos</div>
        <table>
          <thead>
            <tr><th>Fecha y hora</th><th>Evento</th><th>Detalle</th></tr>
          </thead>
          <tbody id="logTable"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    async function refreshData() {
      const res = await fetch('/api/status');
      const data = await res.json();

      document.getElementById('tempValue').textContent = data.temp_c === null ? 'ERROR' : `${data.temp_c.toFixed(1)} °C`;
      document.getElementById('psiValue').textContent = data.psi === null ? 'ERROR' : `${data.psi.toFixed(1)} PSI`;
      document.getElementById('totalHoursValue').textContent = data.total_hours_fmt;
      document.getElementById('oilHoursValue').textContent = data.oil_hours_fmt;
      document.getElementById('voltageValue').textContent = data.voltage === null ? 'ERROR' : `${data.voltage.toFixed(3)} V`;
      document.getElementById('oilChangesValue').textContent = data.oil_changes;
      document.getElementById('lastOilChangeValue').textContent = data.last_oil_change_at || 'Sin registro';
      document.getElementById('timestampBox').textContent = `Última actualización: ${data.timestamp}`;

      const badge = document.getElementById('statusBadge');
      badge.textContent = data.status;
      badge.className = 'status-badge' + (data.status === 'ALERTA' ? ' alert' : '');

      const alarmsBox = document.getElementById('alarmsBox');
      if (data.alarms.length) {
        alarmsBox.innerHTML = `<div class="alarm-list">${data.alarms.map(a => `<div class="alarm">${a}</div>`).join('')}</div>`;
      } else {
        alarmsBox.innerHTML = '<div class="ok-box">Sistema operando normalmente</div>';
      }

      const logRes = await fetch('/api/logs');
      const logs = await logRes.json();
      const tbody = document.getElementById('logTable');
      tbody.innerHTML = logs.map(row => `
        <tr>
          <td>${row.timestamp}</td>
          <td>${row.event}</td>
          <td>${row.details || ''}</td>
        </tr>
      `).join('');
    }

    refreshData();
    setInterval(refreshData, 2000);
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/status")
def api_status():
    return jsonify(current_snapshot())


@app.route("/api/logs")
def api_logs():
    return jsonify(read_last_logs())


@app.route("/maintenance", methods=["POST"])
def maintenance():
    password = request.form.get("password", "")
    action = request.form.get("action", "")

    if password != PASSWORD:
        log_event("AUTH_FAIL", f"maintenance:{action}")
        return "Contraseña incorrecta", 403

    runtime_data = load_runtime()
    runtime_data = update_runtime_hours(runtime_data)

    if action == "reset_oil":
        runtime_data["oil_hours"] = 0.0
        runtime_data["oil_changes"] = runtime_data.get("oil_changes", 0) + 1
        runtime_data["last_oil_change_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        runtime_data["last_reset_by"] = "maintenance"
        log_event("OIL_RESET", "Horas de aceite reiniciadas")
    elif action == "reset_total":
        runtime_data["total_hours"] = 0.0
        runtime_data["last_reset_by"] = "maintenance"
        log_event("TOTAL_RESET", "Horímetro total reiniciado")
    elif action == "reset_both":
        runtime_data["total_hours"] = 0.0
        runtime_data["oil_hours"] = 0.0
        runtime_data["oil_changes"] = runtime_data.get("oil_changes", 0) + 1
        runtime_data["last_oil_change_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        runtime_data["last_reset_by"] = "maintenance"
        log_event("FULL_RESET", "Reinicio completo de horímetros")
    else:
        return "Acción no válida", 400

    save_runtime(runtime_data)
    return redirect(url_for("index"))


if __name__ == "__main__":
    log_event("START", "Interfaz gráfica iniciada")
    app.run(host="0.0.0.0", port=5000, debug=False)
