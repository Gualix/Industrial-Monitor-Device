import glob
import time

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28-*')[0]
device_file = device_folder + '/w1_slave'

def read_temp():
    with open(device_file, 'r') as f:
        lines = f.readlines()

    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        with open(device_file, 'r') as f:
            lines = f.readlines()

    temp_pos = lines[1].find('t=')

    if temp_pos != -1:
        temp_c = float(lines[1][temp_pos+2:]) / 1000.0
        temp_f = temp_c * 9/5 + 32
        return temp_c, temp_f

while True:
    temp_c, temp_f = read_temp()

    print(f"Temperatura: {temp_c:.2f} °C")
    
    if temp_c > 100:
        print("⚠️ ALERTA: Temperatura mayor a 100°C")

    time.sleep(2)