import glob
import os
import smbus
import time
from datetime import datetime

# =========================
# CONFIGURACIÓN
# =========================

ADS1115_ADDR = 0x48
REG_CONVERSION = 0x00
REG_CONFIG = 0x01

# ADS1115:
# A0, rango ±4.096V, modo continuo
ADS_CONFIG = 0x42C3

TEMP_HIGH_LIMIT_C = 100.0
PRESSURE_LOW_LIMIT_PSI = 10.0

# Sensor de presión 0.5V - 4.5V = 0 - 150 PSI
PRESSURE_VOLT_MIN = 0.5
PRESSURE_VOLT_MAX = 4.5
PRESSURE_PSI_MIN = 0.0
PRESSURE_PSI_MAX = 150.0

READ_INTERVAL_SEC = 2

# =========================
# INICIALIZACIÓN
# =========================

bus = smbus.SMBus(1)
start_time = time.time()

# Buscar DS18B20
base_dir = "/sys/bus/w1/devices/"
device_folders = glob.glob(base_dir + "28-*")
device_file = device_folders[0] + "/w1_slave" if device_folders else None


# =========================
# FUNCIONES
# =========================

def clear_screen():
    os.system("clear")


def format_runtime(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def read_temp():
    if not device_file:
        return None

    try:
        with open(device_file, "r") as f:
            lines = f.readlines()

        while lines[0].strip()[-3:] != "YES":
            time.sleep(0.2)
            with open(device_file, "r") as f:
                lines = f.readlines()

        temp_pos = lines[1].find("t=")
        if temp_pos != -1:
            temp_c = float(lines[1][temp_pos + 2:]) / 1000.0
            return temp_c

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

        voltage = raw_adc * 4.096 / 32768.0
        return voltage

    except Exception:
        return None


def voltage_to_psi(voltage):
    if voltage is None:
        return None

    psi = (voltage - PRESSURE_VOLT_MIN) * (
        (PRESSURE_PSI_MAX - PRESSURE_PSI_MIN)
        / (PRESSURE_VOLT_MAX - PRESSURE_VOLT_MIN)
    )

    if psi < 0:
        psi = 0.0
    if psi > PRESSURE_PSI_MAX:
        psi = PRESSURE_PSI_MAX

    return psi


def get_alarm_status(temp_c, psi):
    alarms = []

    if temp_c is None:
        alarms.append("TEMP SENSOR ERROR")
    elif temp_c > TEMP_HIGH_LIMIT_C:
        alarms.append("HIGH TEMP")

    if psi is None:
        alarms.append("PRESSURE SENSOR ERROR")
    elif psi < PRESSURE_LOW_LIMIT_PSI:
        alarms.append("LOW OIL PRESSURE")

    if not alarms:
        return "NORMAL"

    return " | ".join(alarms)


# =========================
# LOOP PRINCIPAL
# =========================

try:
    while True:
        now = datetime.now()
        runtime = time.time() - start_time

        temp_c = read_temp()
        voltage = read_ads_voltage()
        psi = voltage_to_psi(voltage)
        alarm_status = get_alarm_status(temp_c, psi)

        clear_screen()

        print("========================================")
        print("      INDUSTRIAL MONITOR DEVICE")
        print("========================================")
        print(f"Fecha/Hora       : {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Horimetro sesión : {format_runtime(runtime)}")
        print("----------------------------------------")

        if temp_c is not None:
            print(f"Temperatura      : {temp_c:.2f} °C")
        else:
            print("Temperatura      : ERROR")

        if voltage is not None:
            print(f"Voltaje A0       : {voltage:.3f} V")
        else:
            print("Voltaje A0       : ERROR")

        if psi is not None:
            print(f"Presión aceite   : {psi:.2f} PSI")
        else:
            print("Presión aceite   : ERROR")

        print("----------------------------------------")
        print(f"Estado           : {alarm_status}")
        print("========================================")

        time.sleep(READ_INTERVAL_SEC)

except KeyboardInterrupt:
    print("\nMonitor detenido por el usuario.")