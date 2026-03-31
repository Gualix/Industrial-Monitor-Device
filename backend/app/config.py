from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_FILE = DATA_DIR / "runtime.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
LAST_STATE_FILE = DATA_DIR / "last_state.json"

API_HOST = "0.0.0.0"
API_PORT = 5000
POLL_INTERVAL_SECONDS = 1.0

# Display / UI
DISPLAY_SIZE_INCHES = 5

# Hardware
BUZZER_1_GPIO = 18
BUZZER_2_GPIO = 23
DS18B20_GPIO = 4
ADS1115_CHANNEL = 0

# ADS1115 configuration
# gain = 2/3 allows up to 6.144V full scale, useful for a 0.5V-4.5V pressure sensor.
ADS1115_GAIN = 2 / 3

# Pressure sensor scaling
PRESSURE_SENSOR_MIN_V = 0.5
PRESSURE_SENSOR_MAX_V = 4.5
PRESSURE_SENSOR_MIN_PSI = 0.0
PRESSURE_SENSOR_MAX_PSI = 150.0

# Alarm thresholds
TEMP_HIGH_C = 100.0
PRESSURE_LOW_PSI = 10.0
MAINTENANCE_INTERVAL_HOURS = 500.0

# Maintenance access
MAINTENANCE_PASSWORD = "1234"

# Engine detection
ENGINE_ON_PRESSURE_THRESHOLD_PSI = 5.0

# Safety / fallback behavior
ENABLE_HARDWARE_FALLBACKS = True
FALLBACK_TEMPERATURE_C = 28.0
FALLBACK_PRESSURE_VOLTAGE = 0.5
