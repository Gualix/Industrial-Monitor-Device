import glob
import time
import RPi.GPIO as GPIO

# Configuración buzzer
BUZZER = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER, GPIO.OUT)

# Buscar DS18B20
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-*')[0]
device_file = device_folder + '/w1_slave'

def read_temp():
    with open(device_file, 'r') as f:
        lines = f.readlines()

    # esperar lectura válida
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        with open(device_file, 'r') as f:
            lines = f.readlines()

    temp_pos = lines[1].find('t=')

    if temp_pos != -1:
        temp_c = float(lines[1][temp_pos+2:]) / 1000.0
        return temp_c

print("Iniciando monitoreo temperatura...")

try:

    while True:

        temp = read_temp()

        print(f"Temperatura: {temp:.2f} °C")

        if temp > 30:
            GPIO.output(BUZZER, GPIO.HIGH)
            print("ALERTA temperatura alta")
        else:
            GPIO.output(BUZZER, GPIO.LOW)

        time.sleep(2)

except KeyboardInterrupt:

    GPIO.output(BUZZER, GPIO.LOW)
    GPIO.cleanup()
    print("Programa detenido")