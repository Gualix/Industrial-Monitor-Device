# sensors.py
import time
from datetime import datetime

# En el futuro aquí importarás tus librerías del ADC, DS18B20, etc.
# from your_ads_module import leer_presion_real
# from your_temp_module import leer_temp_real

_start_time = time.time()

def get_status():
    """
    Devuelve un diccionario con el estado actual.
    Ahora simula valores. Luego reemplaza por lecturas reales.
    """
    # Simulaciones:
    psi = 40.0 + (time.time() % 20)        # 40–60 PSI
    temp_c = 70.0 + (time.time() % 20)     # 70–90 °C

    # Lógica simple de estado
    if psi < 10 or temp_c > 100:
        state = "ALERT"
    else:
        state = "OK"

    # Horímetro simulado: tiempo desde arranque en horas
    seconds_on = time.time() - _start_time
    hours_on = seconds_on / 3600.0

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "pressure_psi": psi,
        "temperature_c": temp_c,
        "state": state,
        "hours_on": hours_on,
    }