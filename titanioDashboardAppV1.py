from flask import Flask, request, jsonify, render_template_string, redirect, url_for
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
        f.write(f"{now},{event},{details}\n")


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
        time.sleep(0.08)
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


def format_hours_minutes(hours):
    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:05d}:{m:02d}"


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
        "total_hours_fmt": format_hours_minutes(runtime_data["total_hours"]),
        "oil_hours_fmt": format_hours_minutes(runtime_data["oil_hours"]),
    }


HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>TITANIO Monitor</title>
  <style>
    :root {
      --chartreuse: #e0ff4f;
      --gunmetal: #00272b;
      --gunmetal-2: #09363b;
      --bg: #001b1e;
      --panel: #06282d;
      --panel-2: #0c3439;
      --text: #f4ffd3;
      --muted: #a9c6ad;
      --danger: #ff7e7e;
      --ok: #89f3a3;
      --border: rgba(224,255,79,.18);
      --radius: 22px;
      --shadow: 0 10px 25px rgba(0,0,0,.28);
    }

    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); font-family: Inter, system-ui, Arial, sans-serif; }
    body { min-height: 100vh; }

    .app {
      width: 100%;
      min-height: 100vh;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: linear-gradient(180deg, #012126 0%, #00171a 100%);
    }

    .header {
      background: var(--gunmetal);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 14px 16px;
      box-shadow: var(--shadow);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    .title-wrap h1 {
      margin: 0;
      font-size: 1.7rem;
      color: var(--chartreuse);
      line-height: 1;
      letter-spacing: -.03em;
    }

    .title-wrap p {
      margin: 6px 0 0;
      color: var(--muted);
      font-size: .95rem;
    }

    .badge {
      padding: 10px 16px;
      border-radius: 999px;
      font-weight: 800;
      font-size: 1rem;
      background: rgba(224,255,79,.12);
      color: var(--chartreuse);
      border: 1px solid var(--border);
      min-width: 112px;
      text-align: center;
    }

    .badge.alert {
      background: rgba(255,126,126,.14);
      color: #ffd0d0;
      border-color: rgba(255,126,126,.26);
    }

    .tabs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    .tab-btn {
      border: 1px solid var(--border);
      background: var(--gunmetal);
      color: var(--chartreuse);
      border-radius: 18px;
      padding: 16px 12px;
      font-size: 1.05rem;
      font-weight: 800;
      cursor: pointer;
      min-height: 62px;
    }

    .tab-btn.active {
      background: var(--chartreuse);
      color: var(--gunmetal);
    }

    .tab-panel { display: none; }
    .tab-panel.active { display: block; }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 16px;
    }

    .card.full { grid-column: 1 / -1; }

    .label {
      color: var(--muted);
      font-size: .95rem;
      margin-bottom: 10px;
    }

    .value {
      font-size: clamp(2rem, 5vw, 3.4rem);
      font-weight: 900;
      line-height: .95;
      letter-spacing: -.05em;
      color: var(--chartreuse);
      word-break: break-word;
    }

    .value.secondary {
      color: var(--text);
    }

    .sub {
      margin-top: 8px;
      color: var(--muted);
      font-size: .92rem;
    }

    .alarm-list {
      display: grid;
      gap: 10px;
    }

    .alarm {
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(255,126,126,.12);
      border: 1px solid rgba(255,126,126,.22);
      color: #ffe2e2;
      font-size: 1.05rem;
      font-weight: 800;
    }

    .ok-box {
      padding: 14px 16px;
      border-radius: 16px;
      background: rgba(137,243,163,.10);
      border: 1px solid rgba(137,243,163,.2);
      color: var(--ok);
      font-size: 1.05rem;
      font-weight: 800;
    }

    .summary-list {
      display: grid;
      gap: 10px;
    }

    .summary-item {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--panel-2);
      border: 1px solid rgba(224,255,79,.08);
      font-size: 1rem;
    }

    .summary-item strong {
      color: var(--chartreuse);
      font-size: 1.05rem;
    }

    .maintenance-actions {
      display: grid;
      gap: 12px;
      margin-top: 14px;
    }

    .action-btn {
      border: 1px solid var(--border);
      background: var(--gunmetal);
      color: var(--chartreuse);
      border-radius: 18px;
      padding: 18px 16px;
      font-size: 1.05rem;
      font-weight: 800;
      cursor: pointer;
      min-height: 66px;
    }

    .action-btn:active, .tab-btn:active, .key:active, .modal-btn:active {
      transform: scale(.98);
    }

    .logs {
      display: grid;
      gap: 10px;
      max-height: 36vh;
      overflow: auto;
      padding-right: 4px;
    }

    .log-row {
      padding: 14px 16px;
      border-radius: 16px;
      background: var(--panel-2);
      border: 1px solid rgba(224,255,79,.08);
    }

    .log-time {
      color: var(--chartreuse);
      font-weight: 800;
      margin-bottom: 4px;
      font-size: .95rem;
    }

    .log-event { font-weight: 800; margin-bottom: 4px; }
    .log-detail { color: var(--muted); font-size: .92rem; }

    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,.65);
      display: none;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 1000;
    }

    .modal-backdrop.open { display: flex; }

    .modal {
      width: min(520px, 100%);
      background: #032126;
      border: 1px solid var(--border);
      border-radius: 28px;
      padding: 18px;
      box-shadow: 0 25px 50px rgba(0,0,0,.35);
    }

    .modal h3 {
      margin: 0 0 8px;
      color: var(--chartreuse);
      font-size: 1.4rem;
    }

    .modal p {
      margin: 0 0 14px;
      color: var(--muted);
    }

    .pin-display {
      min-height: 68px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 2rem;
      font-weight: 900;
      letter-spacing: .35em;
      color: var(--text);
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 18px;
      margin-bottom: 14px;
      padding-left: .35em;
    }

    .keypad {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
    }

    .key, .modal-btn {
      min-height: 76px;
      border-radius: 18px;
      border: 1px solid var(--border);
      background: var(--gunmetal);
      color: var(--chartreuse);
      font-size: 1.9rem;
      font-weight: 900;
      cursor: pointer;
    }

    .modal-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 14px;
    }

    .modal-btn.primary {
      background: var(--chartreuse);
      color: var(--gunmetal);
      font-size: 1.1rem;
    }

    .modal-btn.secondary {
      font-size: 1.1rem;
    }

    .flash {
      margin-top: 10px;
      padding: 12px 14px;
      border-radius: 14px;
      font-weight: 700;
      display: none;
    }

    .flash.show { display: block; }
    .flash.ok { background: rgba(137,243,163,.10); color: var(--ok); border: 1px solid rgba(137,243,163,.2); }
    .flash.err { background: rgba(255,126,126,.12); color: #ffd0d0; border: 1px solid rgba(255,126,126,.22); }

    @media (max-width: 700px) {
      .grid { grid-template-columns: 1fr; }
      .header { align-items: flex-start; flex-direction: column; }
      .badge { width: 100%; }
      .value { font-size: 2.5rem; }
      .key, .modal-btn { min-height: 84px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <div class="header">
      <div class="title-wrap">
        <h1>TITANIO Monitor</h1>
        <p>Panel principal táctil</p>
      </div>
      <div id="statusBadge" class="badge">Cargando...</div>
    </div>

    <div class="tabs">
      <button class="tab-btn active" data-tab="main">Monitor</button>
      <button class="tab-btn" data-tab="summary">Resumen técnico</button>
    </div>

    <section class="tab-panel active" id="tab-main">
      <div class="grid">
        <div class="card">
          <div class="label">Temperatura</div>
          <div class="value" id="tempValue">--</div>
          <div class="sub">Límite de alarma: 100 °C</div>
        </div>

        <div class="card">
          <div class="label">Presión de aceite</div>
          <div class="value" id="psiValue">--</div>
          <div class="sub">Alarma por debajo de 10 PSI</div>
        </div>

        <div class="card">
          <div class="label">Horímetro total</div>
          <div class="value secondary" id="totalHoursValue">--</div>
          <div class="sub">Formato horas:minutos</div>
        </div>

        <div class="card">
          <div class="label">Desde último cambio de aceite</div>
          <div class="value secondary" id="oilHoursValue">--</div>
          <div class="sub">Alarma a las 500 horas</div>
        </div>

        <div class="card full">
          <div class="label">Estado del sistema</div>
          <div id="alarmsBox"></div>
          <div class="sub" id="timestampBox">--</div>
        </div>
      </div>
    </section>

    <section class="tab-panel" id="tab-summary">
      <div class="grid">
        <div class="card full">
          <div class="label">Resumen técnico</div>
          <div class="summary-list">
            <div class="summary-item"><span>Voltaje ADS1115</span><strong id="voltageValue">--</strong></div>
            <div class="summary-item"><span>Cambios de aceite registrados</span><strong id="oilChangesValue">--</strong></div>
            <div class="summary-item"><span>Último cambio de aceite</span><strong id="lastOilChangeValue">--</strong></div>
            <div class="summary-item"><span>Última actualización</span><strong id="summaryTimestamp">--</strong></div>
          </div>
        </div>

        <div class="card full">
          <div class="label">Mantenimiento</div>
          <div class="maintenance-actions">
            <button class="action-btn" data-action="reset_oil">Reiniciar horas de aceite</button>
            <button class="action-btn" data-action="reset_total">Reiniciar horímetro total</button>
            <button class="action-btn" data-action="reset_both">Reiniciar ambos valores</button>
          </div>
          <div id="flashBox" class="flash"></div>
        </div>

        <div class="card full">
          <div class="label">Últimos eventos</div>
          <div id="logsBox" class="logs"></div>
        </div>
      </div>
    </section>
  </div>

  <div class="modal-backdrop" id="pinModal">
    <div class="modal">
      <h3>Acceso protegido</h3>
      <p>Ingrese la contraseña para continuar.</p>
      <div class="pin-display" id="pinDisplay">&nbsp;</div>
      <div class="keypad">
        <button class="key">1</button>
        <button class="key">2</button>
        <button class="key">3</button>
        <button class="key">4</button>
        <button class="key">5</button>
        <button class="key">6</button>
        <button class="key">7</button>
        <button class="key">8</button>
        <button class="key">9</button>
        <button class="key" id="keyClear">C</button>
        <button class="key">0</button>
        <button class="key" id="keyBack">⌫</button>
      </div>
      <div class="modal-actions">
        <button class="modal-btn secondary" id="cancelModal">Cancelar</button>
        <button class="modal-btn primary" id="confirmModal">Confirmar</button>
      </div>
    </div>
  </div>

  <script>
    let pendingAction = null;
    let enteredPin = '';

    function setActiveTab(tab) {
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
      });
      document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `tab-${tab}`);
      });
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => setActiveTab(btn.dataset.tab));
    });

    function showFlash(message, ok=true) {
      const box = document.getElementById('flashBox');
      box.textContent = message;
      box.className = `flash show ${ok ? 'ok' : 'err'}`;
      setTimeout(() => { box.className = 'flash'; }, 3500);
    }

    function renderPin() {
      const display = document.getElementById('pinDisplay');
      display.innerHTML = enteredPin ? '• '.repeat(enteredPin.length).trim() : '&nbsp;';
    }

    function openPinModal(action) {
      pendingAction = action;
      enteredPin = '';
      renderPin();
      document.getElementById('pinModal').classList.add('open');
    }

    function closePinModal() {
      document.getElementById('pinModal').classList.remove('open');
      enteredPin = '';
      pendingAction = null;
      renderPin();
    }

    document.querySelectorAll('.action-btn').forEach(btn => {
      btn.addEventListener('click', () => openPinModal(btn.dataset.action));
    });

    document.querySelectorAll('.key').forEach(btn => {
      btn.addEventListener('click', () => {
        const value = btn.textContent.trim();
        if (btn.id === 'keyClear') {
          enteredPin = '';
        } else if (btn.id === 'keyBack') {
          enteredPin = enteredPin.slice(0, -1);
        } else if (enteredPin.length < 8) {
          enteredPin += value;
        }
        renderPin();
      });
    });

    document.getElementById('cancelModal').addEventListener('click', closePinModal);

    document.getElementById('confirmModal').addEventListener('click', async () => {
      if (!pendingAction) return;
      const form = new FormData();
      form.append('password', enteredPin);
      form.append('action', pendingAction);

      const res = await fetch('/maintenance', { method: 'POST', body: form });
      if (res.ok) {
        showFlash('Cambio aplicado correctamente.', true);
        closePinModal();
        refreshData();
      } else {
        showFlash('Contraseña incorrecta o acción inválida.', false);
        enteredPin = '';
        renderPin();
      }
    });

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
      document.getElementById('summaryTimestamp').textContent = data.timestamp;

      const badge = document.getElementById('statusBadge');
      badge.textContent = data.status;
      badge.className = 'badge' + (data.status === 'ALERTA' ? ' alert' : '');

      const alarmsBox = document.getElementById('alarmsBox');
      if (data.alarms.length) {
        alarmsBox.innerHTML = `<div class="alarm-list">${data.alarms.map(a => `<div class="alarm">${a}</div>`).join('')}</div>`;
      } else {
        alarmsBox.innerHTML = '<div class="ok-box">Sistema operando normalmente</div>';
      }

      const logRes = await fetch('/api/logs');
      const logs = await logRes.json();
      const logsBox = document.getElementById('logsBox');
      logsBox.innerHTML = logs.map(row => `
        <div class="log-row">
          <div class="log-time">${row.timestamp}</div>
          <div class="log-event">${row.event}</div>
          <div class="log-detail">${row.details || ''}</div>
        </div>
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
    return ("OK", 200)


if __name__ == "__main__":
    log_event("START", "Interfaz gráfica iniciada")
    app.run(host="0.0.0.0", port=5000, debug=False)
