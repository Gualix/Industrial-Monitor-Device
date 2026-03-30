import os
import json
import time
import glob
import smbus
from datetime import datetime

DATA_DIR = "data"
RUNTIME_FILE = f"{DATA_DIR}/runtime.json"
LOG_FILE = f"{DATA_DIR}/log.csv"

PASSWORD = "2026"

OIL_CHANGE_INTERVAL_HOURS = 500

SAVE_INTERVAL = 5
READ_INTERVAL = 2

ADS_ADDR = 0x48

PRESSURE_MIN_V = 0.5
PRESSURE_MAX_V = 4.5
PRESSURE_MAX_PSI = 150

TEMP_LIMIT = 100
PRESSURE_LIMIT = 10

bus = smbus.SMBus(1)

start_time = time.time()
last_save = time.time()

os.makedirs(DATA_DIR, exist_ok=True)

def log_event(event, details=""):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a") as f:
        f.write(f"{now},{event},{details}\n")

def load_runtime():

    if not os.path.exists(RUNTIME_FILE):

        data = {
            "total_hours": 0,
            "oil_hours": 0,
            "last_update": time.time(),
            "oil_changes": 0
        }

        save_runtime(data)
        return data

    with open(RUNTIME_FILE) as f:
        return json.load(f)

def save_runtime(data):

    data["last_update"] = time.time()

    with open(RUNTIME_FILE, "w") as f:
        json.dump(data, f)

runtime_data = load_runtime()

base_dir = "/sys/bus/w1/devices/"
device_folder = glob.glob(base_dir + "28-*")[0]
device_file = device_folder + "/w1_slave"

def read_temp():

    with open(device_file) as f:
        lines = f.readlines()

    temp_pos = lines[1].find("t=")

    if temp_pos != -1:

        return float(lines[1][temp_pos+2:]) / 1000

def read_voltage():

    config = 0x42C3

    bus.write_i2c_block_data(ADS_ADDR, 1,
        [(config >> 8) & 0xFF, config & 0xFF])

    time.sleep(0.1)

    data = bus.read_i2c_block_data(ADS_ADDR, 0, 2)

    raw = data[0] << 8 | data[1]

    if raw > 32767:
        raw -= 65536

    return raw * 4.096 / 32768

def voltage_to_psi(v):

    psi = (v - PRESSURE_MIN_V) * (
        PRESSURE_MAX_PSI / (PRESSURE_MAX_V - PRESSURE_MIN_V)
    )

    if psi < 0:
        psi = 0

    return psi

def clear():
    os.system("clear")

log_event("START")

try:

    while True:

        now = datetime.now()

        elapsed = (time.time() - runtime_data["last_update"]) / 3600

        runtime_data["total_hours"] += elapsed
        runtime_data["oil_hours"] += elapsed

        temp = read_temp()
        volt = read_voltage()
        psi = voltage_to_psi(volt)

        oil_alarm = runtime_data["oil_hours"] >= OIL_CHANGE_INTERVAL_HOURS

        alarm_text = []

        if temp > TEMP_LIMIT:
            alarm_text.append("HIGH TEMP")

        if psi < PRESSURE_LIMIT:
            alarm_text.append("LOW PRESSURE")

        if oil_alarm:
            alarm_text.append("CHANGE OIL")

        clear()

        print("INDUSTRIAL MONITOR DEVICE")
        print("========================")

        print("Hora:", now.strftime("%Y-%m-%d %H:%M:%S"))

        print(f"Horas totales: {runtime_data['total_hours']:.2f}")

        print(f"Horas aceite: {runtime_data['oil_hours']:.2f}")

        print(f"Temperatura: {temp:.2f} C")

        print(f"Presion: {psi:.2f} PSI")

        print("------------------------")

        if alarm_text:

            print("ALARMAS:")
            for a in alarm_text:
                print(a)

        else:
            print("Estado: NORMAL")

        if time.time() - last_save > SAVE_INTERVAL:

            save_runtime(runtime_data)

            last_save = time.time()

        time.sleep(READ_INTERVAL)

except KeyboardInterrupt:

    save_runtime(runtime_data)

    log_event("STOP")
